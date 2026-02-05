-- ============================================================================
-- Adventure Mode SQL Functions
-- ============================================================================
-- Core functions for processing adventure rounds.
-- Run in Supabase SQL Editor or deploy via deploy_adventure_functions.py
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Function: calculate_adventure_round
-- ----------------------------------------------------------------------------
-- Processes a single day's damage to a monster based on task completion.
--
-- Parameters:
--   adventure_uuid: The adventure ID
--   round_date: The date to process
--
-- Returns:
--   TABLE (damage INT, new_hp INT)
--
-- Behavior:
--   - Skips if on break (clears break status if passed)
--   - Returns (0, current_hp) if no tasks planned
--   - Calculates damage from task completion
--   - Updates adventure stats
-- ----------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION calculate_adventure_round(
    adventure_uuid UUID,
    round_date DATE
)
RETURNS TABLE (damage INT, new_hp INT)
LANGUAGE plpgsql
AS $$
DECLARE
    v_adventure RECORD;
    v_entry_id UUID;
    v_mandatory_total INT;
    v_mandatory_completed INT;
    v_optional_completed INT;
    v_damage INT;
    v_new_hp INT;
BEGIN
    -- ===================================================================
    -- TRANSACTION BLOCK with ROW LOCK
    -- Lock adventure row to prevent concurrent processing
    -- ===================================================================

    -- 1. Get adventure with row lock
    SELECT * INTO v_adventure
    FROM adventures
    WHERE id = adventure_uuid
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Adventure not found: %', adventure_uuid;
    END IF;

    -- 2. Handle break status
    IF v_adventure.is_on_break THEN
        IF round_date >= v_adventure.break_end_date THEN
            -- Break has ended, clear status and continue processing
            UPDATE adventures
            SET is_on_break = false,
                break_end_date = NULL
            WHERE id = adventure_uuid;
            -- Fall through to normal processing below
        ELSE
            -- Still on break, return 0 damage
            RETURN QUERY SELECT 0, v_adventure.monster_current_hp;
            RETURN;
        END IF;
    END IF;

    -- 3. Get daily entry for this date
    SELECT id INTO v_entry_id
    FROM daily_entries
    WHERE adventure_id = adventure_uuid AND date = round_date;

    IF v_entry_id IS NULL THEN
        -- No tasks planned for this day (0 damage)
        RETURN QUERY SELECT 0, v_adventure.monster_current_hp;
        RETURN;
    END IF;

    -- 4. Count tasks
    SELECT
        COUNT(*) FILTER (WHERE NOT is_optional),
        COUNT(*) FILTER (WHERE is_completed AND NOT is_optional),
        COUNT(*) FILTER (WHERE is_completed AND is_optional)
    INTO v_mandatory_total, v_mandatory_completed, v_optional_completed
    FROM tasks
    WHERE daily_entry_id = v_entry_id;

    -- 5. Calculate damage (capped at 120)
    IF v_mandatory_total > 0 THEN
        v_damage := LEAST(
            (v_mandatory_completed::FLOAT / v_mandatory_total * 100)::INT + (v_optional_completed * 10),
            120
        );
    ELSE
        v_damage := LEAST(v_optional_completed * 10, 120);
    END IF;

    -- 6. Apply damage to monster (floor at 0)
    v_new_hp := GREATEST(v_adventure.monster_current_hp - v_damage, 0);

    -- 7. Update adventure
    UPDATE adventures
    SET monster_current_hp = v_new_hp,
        total_damage_dealt = total_damage_dealt + v_damage,
        current_round = current_round + 1
    WHERE id = adventure_uuid;

    -- 8. Store damage in daily entry (for history)
    UPDATE daily_entries
    SET daily_xp = v_damage
    WHERE id = v_entry_id;

    -- 9. Return results
    RETURN QUERY SELECT v_damage, v_new_hp;

EXCEPTION
    WHEN OTHERS THEN
        RAISE EXCEPTION 'calculate_adventure_round failed for adventure % on date %: %',
            adventure_uuid, round_date, SQLERRM;
END;
$$;

-- Add comment for documentation
COMMENT ON FUNCTION calculate_adventure_round IS 'Processes a single day''s damage to a monster. Returns (damage, new_hp). Skips break days.';
