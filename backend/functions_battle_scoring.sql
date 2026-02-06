-- SQL Functions for battle scoring system

-- Function to calculate daily XP and determine daily winner
-- BUG-005 FIX: Added explicit transaction block for atomicity
CREATE OR REPLACE FUNCTION calculate_daily_round(
    battle_uuid UUID,
    round_date DATE
)
RETURNS TABLE(user1_xp INT, user2_xp INT, winner_id UUID)
LANGUAGE plpgsql
AS $$
DECLARE
    v_user1_id UUID;
    v_user2_id UUID;
    v_quota INT;
    v_user1_xp INT;
    v_user2_xp INT;
    v_winner_id UUID;
BEGIN
    -- ===================================================================
    -- TRANSACTION BLOCK
    -- All updates below succeed together or fail together
    -- ===================================================================

    -- Get battle users with row lock to prevent concurrent processing
    SELECT user1_id, user2_id INTO v_user1_id, v_user2_id
    FROM battles
    WHERE id = battle_uuid
    FOR UPDATE;

    -- Calculate quota for this date
    v_quota := (('x' || substring(md5(round_date::text), 1, 8))::bit(32)::int % 3) + 3;

    -- Calculate XP for both users
    SELECT COALESCE(
        (COUNT(*) FILTER (WHERE NOT is_optional AND is_completed)::DECIMAL / v_quota * 100)
        + (COUNT(*) FILTER (WHERE is_optional AND is_completed) * 10),
        0
    )::INT INTO v_user1_xp
    FROM tasks t
    JOIN daily_entries de ON de.id = t.daily_entry_id
    WHERE de.user_id = v_user1_id AND de.date = round_date;

    SELECT COALESCE(
        (COUNT(*) FILTER (WHERE NOT is_optional AND is_completed)::DECIMAL / v_quota * 100)
        + (COUNT(*) FILTER (WHERE is_optional AND is_completed) * 10),
        0
    )::INT INTO v_user2_xp
    FROM tasks t
    JOIN daily_entries de ON de.id = t.daily_entry_id
    WHERE de.user_id = v_user2_id AND de.date = round_date;

    -- Note: completed_tasks is now automatically updated by trigger
    -- (trigger_update_completed_tasks on tasks table)

    -- Determine winner
    IF v_user1_xp > v_user2_xp THEN
        v_winner_id := v_user1_id;
    ELSIF v_user2_xp > v_user1_xp THEN
        v_winner_id := v_user2_id;
    ELSE
        v_winner_id := NULL; -- Draw
    END IF;

    -- ===================================================================
    -- ATOMIC UPDATES (all in one transaction)
    -- If any update fails, all are rolled back
    -- ===================================================================

    -- Update daily_entries with XP
    UPDATE daily_entries SET daily_xp = v_user1_xp WHERE user_id = v_user1_id AND date = round_date;
    UPDATE daily_entries SET daily_xp = v_user2_xp WHERE user_id = v_user2_id AND date = round_date;

    -- Note: completed_tasks is now automatically updated by trigger
    -- (trigger_update_completed_tasks on tasks table)

    -- Return results
    RETURN QUERY SELECT v_user1_xp, v_user2_xp, v_winner_id;

EXCEPTION
    WHEN OTHERS THEN
        -- Rollback happens automatically in PL/pgSQL
        -- Re-raise the exception with context
        RAISE EXCEPTION 'calculate_daily_round failed for battle % on date %: %',
            battle_uuid, round_date, SQLERRM;
END;
$$;

-- Function to complete battle and determine overall winner
-- BUG-001 FIX: Made idempotent to prevent duplicate stat increments from concurrent calls
-- BUG-005 FIX: Added explicit transaction block and row locking
CREATE OR REPLACE FUNCTION complete_battle(
    battle_uuid UUID
)
RETURNS TABLE(winner_id UUID, user1_total_xp INT, user2_total_xp INT, already_completed BOOLEAN)
LANGUAGE plpgsql
AS $$
DECLARE
    v_user1_id UUID;
    v_user2_id UUID;
    v_user1_total_xp INT;
    v_user2_total_xp INT;
    v_winner_id UUID;
    v_start_date DATE;
    v_end_date DATE;
    v_current_status TEXT;
BEGIN
    -- ===================================================================
    -- TRANSACTION BLOCK with ROW LOCK
    -- Lock the battle row to prevent concurrent completions
    -- ===================================================================

    -- Get current battle details with row lock
    SELECT status, winner_id, user1_id, user2_id, start_date, end_date
    INTO v_current_status, v_winner_id, v_user1_id, v_user2_id, v_start_date, v_end_date
    FROM battles
    WHERE id = battle_uuid
    FOR UPDATE;

    -- Check if battle exists
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Battle not found';
    END IF;

    -- If battle is already completed, return existing result WITHOUT reprocessing (IDEMPOTENCY)
    IF v_current_status = 'completed' THEN
        -- Get the XP values that were already calculated
        SELECT COALESCE(SUM(daily_xp), 0)::INT INTO v_user1_total_xp
        FROM daily_entries
        WHERE user_id = v_user1_id AND date BETWEEN v_start_date AND v_end_date;

        SELECT COALESCE(SUM(daily_xp), 0)::INT INTO v_user2_total_xp
        FROM daily_entries
        WHERE user_id = v_user2_id AND date BETWEEN v_start_date AND v_end_date;

        -- Return already_completed = TRUE to signal this was an idempotent call
        RETURN QUERY SELECT v_winner_id, v_user1_total_xp, v_user2_total_xp, TRUE::BOOLEAN;
        RETURN;
    END IF;

    -- ===================================================================
    -- ATOMIC UPDATES (all in one transaction)
    -- If any update fails, all are rolled back
    -- ===================================================================

    -- Sum total XP across all days
    SELECT COALESCE(SUM(daily_xp), 0)::INT INTO v_user1_total_xp
    FROM daily_entries
    WHERE user_id = v_user1_id AND date BETWEEN v_start_date AND v_end_date;

    SELECT COALESCE(SUM(daily_xp), 0)::INT INTO v_user2_total_xp
    FROM daily_entries
    WHERE user_id = v_user2_id AND date BETWEEN v_start_date AND v_end_date;

    -- Determine overall winner
    IF v_user1_total_xp > v_user2_total_xp THEN
        v_winner_id := v_user1_id;
    ELSIF v_user2_total_xp > v_user1_total_xp THEN
        v_winner_id := v_user2_id;
    ELSE
        v_winner_id := NULL; -- Draw
    END IF;

    -- Update battle_win_count (formerly overall_win_count)
    IF v_winner_id IS NOT NULL THEN
        UPDATE profiles SET battle_win_count = battle_win_count + 1 WHERE id = v_winner_id;
    END IF;

    -- Update total_xp_earned for both
    UPDATE profiles SET total_xp_earned = total_xp_earned + v_user1_total_xp WHERE id = v_user1_id;
    UPDATE profiles SET total_xp_earned = total_xp_earned + v_user2_total_xp WHERE id = v_user2_id;

    -- Increment battle_count for both
    UPDATE profiles SET battle_count = battle_count + 1 WHERE id IN (v_user1_id, v_user2_id);

    -- Note: level is now a generated column (FLOOR(total_xp_earned / 1000) + 1)
    -- It updates automatically when total_xp_earned changes

    -- Mark battle complete WITH timestamp for idempotency
    UPDATE battles
    SET status = 'completed',
        winner_id = v_winner_id,
        completed_at = NOW()
    WHERE id = battle_uuid;

    -- Clean up daily_entries for this battle
    -- Tasks are auto-deleted via CASCADE (item 7.2, 8.3)
    DELETE FROM daily_entries
    WHERE battle_id = battle_uuid;

    -- Return already_completed = FALSE to signal this was a fresh completion
    RETURN QUERY SELECT v_winner_id, v_user1_total_xp, v_user2_total_xp, FALSE::BOOLEAN;

EXCEPTION
    WHEN OTHERS THEN
        -- Rollback happens automatically in PL/pgSQL
        RAISE EXCEPTION 'complete_battle failed for battle %: %', battle_uuid, SQLERRM;
END;
$$;
