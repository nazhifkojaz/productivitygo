-- SQL Functions for battle scoring system

-- Function to calculate daily XP and determine daily winner
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
    -- Get battle users
    SELECT user1_id, user2_id INTO v_user1_id, v_user2_id
    FROM battles WHERE id = battle_uuid;
    
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
    
    -- Determine winner
    IF v_user1_xp > v_user2_xp THEN
        v_winner_id := v_user1_id;
    ELSIF v_user2_xp > v_user1_xp THEN
        v_winner_id := v_user2_id;
    ELSE
        v_winner_id := NULL; -- Draw
    END IF;
    
    -- Update daily_entries with XP
    UPDATE daily_entries SET daily_xp = v_user1_xp WHERE user_id = v_user1_id AND date = round_date;
    UPDATE daily_entries SET daily_xp = v_user2_xp WHERE user_id = v_user2_id AND date = round_date;
    
    -- Update stats
    UPDATE profiles SET 
        completed_tasks = completed_tasks + (SELECT COUNT(*) FROM tasks t JOIN daily_entries de ON de.id = t.daily_entry_id WHERE de.user_id = v_user1_id AND de.date = round_date AND t.is_completed = true)
    WHERE id = v_user1_id;
    
    UPDATE profiles SET 
        completed_tasks = completed_tasks + (SELECT COUNT(*) FROM tasks t JOIN daily_entries de ON de.id = t.daily_entry_id WHERE de.user_id = v_user2_id AND de.date = round_date AND t.is_completed = true)
    WHERE id = v_user2_id;
    
    -- Update daily_win_count (REMOVED: Column deprecated)
    -- IF v_winner_id IS NOT NULL THEN
    --    UPDATE profiles SET daily_win_count = daily_win_count + 1 WHERE id = v_winner_id;
    -- END IF;
    
    RETURN QUERY SELECT v_user1_xp, v_user2_xp, v_winner_id;
END;
$$;

-- Function to complete battle and determine overall winner
-- BUG-001 FIX: Made idempotent to prevent duplicate stat increments from concurrent calls
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
    -- Get current battle details and status first (IDEMPOTENCY CHECK)
    SELECT status, winner_id, user1_id, user2_id, start_date, end_date
    INTO v_current_status, v_winner_id, v_user1_id, v_user2_id, v_start_date, v_end_date
    FROM battles WHERE id = battle_uuid;

    -- If battle is already completed, return existing result WITHOUT reprocessing
    IF v_current_status = 'completed' THEN
        -- Get the XP values that were already calculated
        SELECT COALESCE(SUM(daily_xp), 0)::INT INTO v_user1_total_xp
        FROM daily_entries
        WHERE user_id = v_user1_id AND date BETWEEN v_start_date AND v_end_date;

        SELECT COALESCE(SUM(daily_xp), 0)::INT INTO v_user2_total_xp
        FROM daily_entries
        WHERE user_id = v_user2_id AND date BETWEEN v_start_date AND v_end_date;

        -- Return already_completed = TRUE to signal this was an idempotent call
        RETURN QUERY SELECT v_winner_id, v_user1_total_xp, v_user2_total_xp, TRUE;
        RETURN;
    END IF;

    -- NEW COMPLETION: Process the battle completion
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

    -- Update level (every 1000 XP = 1 level)
    UPDATE profiles SET level = FLOOR(total_xp_earned / 1000) + 1 WHERE id = v_user1_id;
    UPDATE profiles SET level = FLOOR(total_xp_earned / 1000) + 1 WHERE id = v_user2_id;

    -- Mark battle complete WITH timestamp for idempotency
    UPDATE battles
    SET status = 'completed',
        winner_id = v_winner_id,
        completed_at = NOW()
    WHERE id = battle_uuid;

    -- Return already_completed = FALSE to signal this was a fresh completion
    RETURN QUERY SELECT v_winner_id, v_user1_total_xp, v_user2_total_xp, FALSE;
END;
$$;
