-- ============================================================================
-- Adventure Mode Completion Functions
-- ============================================================================
-- Functions for finalizing adventures (victory, escape, or abandonment).
-- Run in Supabase SQL Editor or deploy via deploy_adventure_completion.py
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Function: complete_adventure
-- ----------------------------------------------------------------------------
-- Finalizes an adventure when the deadline passes or monster HP reaches 0.
--
-- Parameters:
--   adventure_uuid UUID - The adventure to complete
--
-- Returns:
--   TABLE (status TEXT, is_victory BOOLEAN, xp_earned INT, already_completed BOOLEAN)
--
-- Behavior:
--   - Victory if monster HP <= 0, else escape
--   - Victory: 100% XP with tier multiplier, +1 rating
--   - Escape: 50% XP with tier multiplier, -1 rating
--   - Idempotent: safe to call multiple times
--   - Updates user profile stats
--   - Clears current_adventure reference
-- ----------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION complete_adventure(
    adventure_uuid UUID
)
RETURNS TABLE (
    status TEXT,
    is_victory BOOLEAN,
    xp_earned INT,
    already_completed BOOLEAN
) AS $$
DECLARE
    v_adv_id UUID;
    v_user_id UUID;
    v_adv_status TEXT;
    v_adv_xp INT;
    v_current_hp INT;
    v_total_damage INT;
    v_is_victory BOOLEAN;
    v_final_xp INT;
    v_multiplier FLOAT;
    v_tier TEXT;
    v_current_highest TEXT;
    v_new_highest TEXT;
BEGIN
    -- ===================================================================
    -- TRANSACTION BLOCK with ROW LOCK
    -- Lock adventure row to prevent concurrent completions
    -- ===================================================================

    -- Get adventure with monster tier (row lock)
    SELECT
        a.id, a.user_id, a.status, a.xp_earned, a.monster_current_hp,
        a.total_damage_dealt, m.tier
    INTO v_adv_id, v_user_id, v_adv_status, v_adv_xp, v_current_hp,
         v_total_damage, v_tier
    FROM adventures a
    JOIN monsters m ON a.monster_id = m.id
    WHERE a.id = adventure_uuid
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Adventure not found: %', adventure_uuid;
    END IF;

    -- Check if already completed (idempotent)
    IF v_adv_status != 'active' THEN
        RETURN QUERY SELECT
            v_adv_status::TEXT,
            v_adv_status = 'completed',
            v_adv_xp::INT,
            TRUE::BOOLEAN;
        RETURN;
    END IF;

    -- Determine outcome
    v_is_victory := v_current_hp <= 0;

    -- Calculate tier multiplier
    v_multiplier := CASE v_tier
        WHEN 'easy' THEN 1.0
        WHEN 'medium' THEN 1.2
        WHEN 'hard' THEN 1.5
        WHEN 'expert' THEN 2.0
        WHEN 'boss' THEN 3.0
        ELSE 1.0
    END;

    -- Calculate XP
    v_final_xp := (v_total_damage * v_multiplier *
                   CASE WHEN v_is_victory THEN 1.0 ELSE 0.5 END)::INT;

    -- Update adventure
    UPDATE adventures SET
        status = CASE WHEN v_is_victory THEN 'completed' ELSE 'escaped' END,
        xp_earned = v_final_xp,
        completed_at = NOW()
    WHERE id = v_adv_id;

    -- Get current highest tier
    SELECT COALESCE(highest_tier_reached, 'easy') INTO v_current_highest
    FROM profiles
    WHERE id = v_user_id;

    -- Calculate new highest tier (only increases on victory)
    IF v_is_victory THEN
        v_new_highest := CASE
            WHEN v_tier = 'boss' THEN 'boss'
            WHEN v_tier = 'expert' AND v_current_highest NOT IN ('boss', 'expert') THEN 'expert'
            WHEN v_tier = 'hard' AND v_current_highest NOT IN ('boss', 'expert', 'hard') THEN 'hard'
            WHEN v_tier = 'medium' AND v_current_highest = 'easy' THEN 'medium'
            ELSE v_current_highest
        END;
    ELSE
        v_new_highest := v_current_highest;
    END IF;

    -- Update user profile stats
    UPDATE profiles SET
        adventure_count = adventure_count + 1,
        adventure_win_count = adventure_win_count + CASE WHEN v_is_victory THEN 1 ELSE 0 END,
        monster_defeats = monster_defeats + CASE WHEN v_is_victory THEN 1 ELSE 0 END,
        monster_escapes = monster_escapes + CASE WHEN NOT v_is_victory THEN 1 ELSE 0 END,
        monster_rating = GREATEST(monster_rating + CASE WHEN v_is_victory THEN 1 ELSE -1 END, 0),
        total_xp_earned = total_xp_earned + v_final_xp,
        total_damage_dealt = COALESCE(total_damage_dealt, 0) + v_total_damage,
        current_adventure = NULL,
        highest_tier_reached = v_new_highest
    WHERE id = v_user_id;

    RETURN QUERY SELECT
        CASE WHEN v_is_victory THEN 'completed' ELSE 'escaped' END::TEXT,
        v_is_victory,
        v_final_xp,
        FALSE::BOOLEAN;

EXCEPTION
    WHEN OTHERS THEN
        RAISE EXCEPTION 'complete_adventure failed for adventure %: %',
            adventure_uuid, SQLERRM;
END;
$$ LANGUAGE plpgsql;

-- Add comment for documentation
COMMENT ON FUNCTION complete_adventure IS 'Finalizes an adventure. Victory if HP<=0, else escape. Updates user stats. Idempotent.';


-- ----------------------------------------------------------------------------
-- Function: abandon_adventure
-- ----------------------------------------------------------------------------
-- Allows user to abandon an active adventure early with 50% XP reward.
--
-- Parameters:
--   adventure_uuid UUID - The adventure to abandon
--   abandoning_user UUID - The user abandoning (must be adventure owner)
--
-- Returns:
--   TABLE (status TEXT, xp_earned INT)
--
-- Behavior:
--   - Verifies ownership (only owner can abandon)
--   - Verifies active status
--   - Rewards 50% XP with tier multiplier
--   - Counts as escape (-1 rating)
--   - Not idempotent (can only abandon once)
-- ----------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION abandon_adventure(
    adventure_uuid UUID,
    abandoning_user UUID
)
RETURNS TABLE (
    status TEXT,
    xp_earned INT
) AS $$
DECLARE
    v_adv_id UUID;
    v_user_id UUID;
    v_adv_status TEXT;
    v_total_damage INT;
    v_multiplier FLOAT;
    v_final_xp INT;
    v_tier TEXT;
BEGIN
    -- ===================================================================
    -- TRANSACTION BLOCK with ROW LOCK
    -- Lock adventure row to prevent concurrent operations
    -- ===================================================================

    -- Get adventure with tier (row lock)
    SELECT
        a.id, a.user_id, a.status, a.total_damage_dealt, m.tier
    INTO v_adv_id, v_user_id, v_adv_status, v_total_damage, v_tier
    FROM adventures a
    JOIN monsters m ON a.monster_id = m.id
    WHERE a.id = adventure_uuid
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Adventure not found: %', adventure_uuid;
    END IF;

    -- Verify ownership
    IF v_user_id != abandoning_user THEN
        RAISE EXCEPTION 'Not your adventure';
    END IF;

    -- Verify active status
    IF v_adv_status != 'active' THEN
        RAISE EXCEPTION 'Adventure is not active (current status: %)', v_adv_status;
    END IF;

    -- Calculate tier multiplier
    v_multiplier := CASE v_tier
        WHEN 'easy' THEN 1.0
        WHEN 'medium' THEN 1.2
        WHEN 'hard' THEN 1.5
        WHEN 'expert' THEN 2.0
        WHEN 'boss' THEN 3.0
        ELSE 1.0
    END;

    -- Calculate 50% XP
    v_final_xp := (v_total_damage * v_multiplier * 0.5)::INT;

    -- Update adventure
    UPDATE adventures SET
        status = 'escaped',
        xp_earned = v_final_xp,
        completed_at = NOW()
    WHERE id = v_adv_id;

    -- Update user profile (counts as escape/loss)
    UPDATE profiles SET
        adventure_count = adventure_count + 1,
        monster_escapes = monster_escapes + 1,
        monster_rating = GREATEST(monster_rating - 1, 0),
        total_xp_earned = total_xp_earned + v_final_xp,
        total_damage_dealt = COALESCE(total_damage_dealt, 0) + v_total_damage,
        current_adventure = NULL
    WHERE id = abandoning_user;

    RETURN QUERY SELECT 'escaped'::TEXT, v_final_xp;

EXCEPTION
    WHEN OTHERS THEN
        RAISE EXCEPTION 'abandon_adventure failed for adventure %: %',
            adventure_uuid, SQLERRM;
END;
$$ LANGUAGE plpgsql;

-- Add comment for documentation
COMMENT ON FUNCTION abandon_adventure IS 'Abandon an active adventure early. Rewards 50% XP. Counts as escape (-1 rating). User must be adventure owner.';
