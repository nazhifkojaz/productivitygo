-- Migration 002: Update Adventure Damage Calculation with Category Multipliers
--
-- This migration updates the calculate_adventure_round function to implement
-- per-task category-based damage multipliers as part of Phase 3.
--
-- Changes:
-- 1. Rewrites calculate_adventure_round to loop through completed tasks individually
-- 2. Each task calculates its own damage based on type effectiveness
-- 3. Records discoveries in type_discoveries table
-- 4. Raises damage cap from 120 to 180
--
-- Prerequisites:
--   - Migration 001 must be applied (type_effectiveness table exists)
--
-- Usage:
--   psql -U postgres -d your_database -f migrations/002_update_adventure_damage_calculation.sql
--
-- Rollback:
--   Restore the previous version of calculate_adventure_round from schema_full.sql backup

-- ----------------------------------------------------------------------------
-- Drop and recreate calculate_adventure_round with new category-based logic
-- ----------------------------------------------------------------------------
DROP FUNCTION IF EXISTS calculate_adventure_round(UUID, DATE);

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
    v_monster_type TEXT;
    v_mandatory_total INT;
    v_task_record RECORD;
    v_task_base_damage NUMERIC;
    v_multiplier NUMERIC;
    v_effectiveness TEXT;
    v_total_damage NUMERIC := 0;
    v_damage INT;
    v_new_hp INT;
BEGIN
    -- Get monster type first
    SELECT m.monster_type INTO v_monster_type
    FROM monsters m
    JOIN adventures a ON a.monster_id = m.id
    WHERE a.id = adventure_uuid;

    -- Get adventure with row lock
    SELECT * INTO v_adventure
    FROM adventures
    WHERE id = adventure_uuid
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Adventure not found: %', adventure_uuid;
    END IF;

    -- Handle break status
    IF v_adventure.is_on_break THEN
        IF round_date >= v_adventure.break_end_date THEN
            UPDATE adventures
            SET is_on_break = false, break_end_date = NULL
            WHERE id = adventure_uuid;
        ELSE
            RETURN QUERY SELECT 0, v_adventure.monster_current_hp;
            RETURN;
        END IF;
    END IF;

    -- Get daily entry for this date
    SELECT id INTO v_entry_id
    FROM daily_entries
    WHERE adventure_id = adventure_uuid AND date = round_date;

    IF v_entry_id IS NULL THEN
        RETURN QUERY SELECT 0, v_adventure.monster_current_hp;
        RETURN;
    END IF;

    -- Count total mandatory tasks (for base damage calculation)
    SELECT COUNT(*) FILTER (WHERE NOT is_optional)
    INTO v_mandatory_total
    FROM tasks
    WHERE daily_entry_id = v_entry_id;

    -- Loop through each COMPLETED task and calculate damage individually
    FOR v_task_record IN
        SELECT t.id, t.category, t.is_optional, t.is_completed
        FROM tasks t
        WHERE t.daily_entry_id = v_entry_id AND t.is_completed = true
    LOOP
        -- Calculate base damage for this task
        IF v_task_record.is_optional THEN
            v_task_base_damage := 10;
        ELSE
            -- Avoid division by zero
            IF v_mandatory_total > 0 THEN
                v_task_base_damage := 100::NUMERIC / v_mandatory_total;
            ELSE
                v_task_base_damage := 0;
            END IF;
        END IF;

        -- Get type multiplier from type_effectiveness table
        -- NULL category or missing entry defaults to 1.0 (neutral)
        SELECT COALESCE(te.multiplier, 1.0)
        INTO v_multiplier
        FROM type_effectiveness te
        WHERE te.monster_type = v_monster_type
          AND te.task_category = v_task_record.category;

        -- Accumulate damage
        v_total_damage := v_total_damage + (v_task_base_damage * v_multiplier);

        -- Determine effectiveness for discovery recording
        IF v_multiplier >= 1.5 THEN
            v_effectiveness := 'super_effective';
        ELSIF v_multiplier <= 0.5 THEN
            v_effectiveness := 'resisted';
        ELSE
            v_effectiveness := 'neutral';
        END IF;

        -- Record discovery (idempotent via ON CONFLICT)
        -- Only record if we have a valid category
        IF v_task_record.category IS NOT NULL THEN
            INSERT INTO type_discoveries (user_id, monster_type, task_category, effectiveness, discovered_at)
            VALUES (v_adventure.user_id, v_monster_type, v_task_record.category, v_effectiveness, now())
            ON CONFLICT (user_id, monster_type, task_category) DO NOTHING;
        END IF;
    END LOOP;

    -- Finalize damage: floor and cap at 180 (raised from 120 for SE bonus)
    v_damage := LEAST(FLOOR(v_total_damage), 180)::INT;

    -- Apply damage (floor at 0)
    v_new_hp := GREATEST(v_adventure.monster_current_hp - v_damage, 0);

    -- Update adventure
    UPDATE adventures
    SET monster_current_hp = v_new_hp,
        total_damage_dealt = total_damage_dealt + v_damage,
        current_round = current_round + 1
    WHERE id = adventure_uuid;

    -- Store damage in daily entry
    UPDATE daily_entries SET daily_xp = v_damage WHERE id = v_entry_id;

    RETURN QUERY SELECT v_damage, v_new_hp;

EXCEPTION
    WHEN OTHERS THEN
        RAISE EXCEPTION 'calculate_adventure_round failed for adventure % on date %: %',
            adventure_uuid, round_date, SQLERRM;
END;
$$;

-- ----------------------------------------------------------------------------
-- Verification
-- ----------------------------------------------------------------------------
-- Verify function exists
-- SELECT proname FROM pg_proc WHERE proname = 'calculate_adventure_round';

-- Test with a real adventure (replace UUID)
-- SELECT * FROM calculate_adventure_round('your-adventure-uuid'::UUID, '2026-02-11'::DATE);
