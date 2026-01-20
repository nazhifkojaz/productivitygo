-- SQL Functions for atomic battle operations
-- BUG-005 Fix: Non-atomic profile stat updates
-- These functions ensure all related updates happen in a single transaction

-- ===================================================================
-- ATOMIC FORFEIT FUNCTION
-- ===================================================================
-- Handles battle forfeiture atomically:
-- 1. Locks battle row with FOR UPDATE (prevents race conditions)
-- 2. Validates battle is active
-- 3. Updates battle status, winner profile, and loser profile
-- 4. All updates succeed or all are rolled back
-- ===================================================================
CREATE OR REPLACE FUNCTION forfeit_battle_atomic(
    battle_uuid UUID,
    forfeiting_user UUID
)
RETURNS TABLE(winner_id UUID, already_completed BOOLEAN)
LANGUAGE plpgsql
AS $$
DECLARE
    v_user1_id UUID;
    v_user2_id UUID;
    v_winner_id UUID;
    v_current_status TEXT;
    v_loser_id UUID;
    v_forfeiting_is_user1 BOOLEAN;
BEGIN
    -- BEGIN TRANSACTION (implicit in PL/pgSQL function)

    -- Lock the battle row to prevent concurrent forfeits
    -- FOR UPDATE locks the row until the transaction completes
    SELECT status, user1_id, user2_id
    INTO v_current_status, v_user1_id, v_user2_id
    FROM battles
    WHERE id = battle_uuid
    FOR UPDATE;

    -- Check if battle exists
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Battle not found';
    END IF;

    -- Check if already completed (idempotency)
    IF v_current_status = 'completed' THEN
        -- Return already_completed = TRUE without making changes
        -- Get the existing winner
        SELECT winner_id INTO v_winner_id
        FROM battles
        WHERE id = battle_uuid;

        RETURN QUERY SELECT v_winner_id, TRUE::BOOLEAN;
        RETURN;
    END IF;

    -- Validate battle is active
    IF v_current_status != 'active' THEN
        RAISE EXCEPTION 'Can only forfeit active battles, current status: %', v_current_status;
    END IF;

    -- Validate the forfeiting user is a participant
    IF forfeiting_user != v_user1_id AND forfeiting_user != v_user2_id THEN
        RAISE EXCEPTION 'User is not a participant in this battle';
    END IF;

    -- Determine winner (the OTHER person)
    v_forfeiting_is_user1 := (forfeiting_user = v_user1_id);
    IF v_forfeiting_is_user1 THEN
        v_winner_id := v_user2_id;
        v_loser_id := v_user1_id;
    ELSE
        v_winner_id := v_user1_id;
        v_loser_id := v_user2_id;
    END IF;

    -- ===================================================================
    -- ATOMIC UPDATES (all in one transaction)
    -- If any update fails, all changes are rolled back
    -- ===================================================================

    -- 1. Update battle status
    UPDATE battles
    SET status = 'completed',
        winner_id = v_winner_id,
        end_date = CURRENT_DATE,
        completed_at = NOW()
    WHERE id = battle_uuid;

    -- 2. Update winner profile (increment both win count and battle count)
    UPDATE profiles
    SET battle_win_count = battle_win_count + 1,
        battle_count = battle_count + 1
    WHERE id = v_winner_id;

    -- 3. Update loser profile (increment battle count only)
    UPDATE profiles
    SET battle_count = battle_count + 1
    WHERE id = v_loser_id;

    -- COMMIT TRANSACTION (implicit in PL/pgSQL function)

    -- Return success
    RETURN QUERY SELECT v_winner_id, FALSE::BOOLEAN;

EXCEPTION
    WHEN OTHERS THEN
        -- ROLLBACK on any error (implicit in PL/pgSQL)
        RAISE;
END;
$$;


-- ===================================================================
-- ATOMIC BATTLE ACCEPT FUNCTION
-- ===================================================================
-- Handles battle invitation acceptance atomically:
-- 1. Validates battle is pending and user is the invitee
-- 2. Updates battle status to active
-- 3. Sets current_battle for both users
-- 4. All updates succeed or all are rolled back
-- ===================================================================
CREATE OR REPLACE FUNCTION accept_battle_atomic(
    battle_uuid UUID,
    accepting_user UUID
)
RETURNS TABLE(success BOOLEAN, error_message TEXT)
LANGUAGE plpgsql
AS $$
DECLARE
    v_user1_id UUID;
    v_user2_id UUID;
    v_current_status TEXT;
BEGIN
    -- BEGIN TRANSACTION (implicit in PL/pgSQL function)

    -- Lock the battle row
    SELECT status, user1_id, user2_id
    INTO v_current_status, v_user1_id, v_user2_id
    FROM battles
    WHERE id = battle_uuid
    FOR UPDATE;

    -- Check if battle exists
    IF NOT FOUND THEN
        RETURN QUERY SELECT FALSE::BOOLEAN, 'Battle not found'::TEXT;
        RETURN;
    END IF;

    -- Validate the accepting user is the invitee (user2)
    IF accepting_user != v_user2_id THEN
        RETURN QUERY SELECT FALSE::BOOLEAN, 'Not your invite to accept'::TEXT;
        RETURN;
    END IF;

    -- Validate battle is pending
    IF v_current_status != 'pending' THEN
        RETURN QUERY SELECT FALSE::BOOLEAN, 'Invite not pending (status: ' || v_current_status || ')'::TEXT;
        RETURN;
    END IF;

    -- ===================================================================
    -- ATOMIC UPDATES
    -- ===================================================================

    -- 1. Update battle status to active
    UPDATE battles
    SET status = 'active'
    WHERE id = battle_uuid;

    -- 2. Set current_battle for both users
    UPDATE profiles
    SET current_battle = battle_uuid
    WHERE id = v_user1_id;

    UPDATE profiles
    SET current_battle = battle_uuid
    WHERE id = v_user2_id;

    -- COMMIT TRANSACTION (implicit)

    RETURN QUERY SELECT TRUE::BOOLEAN, NULL::TEXT;

EXCEPTION
    WHEN OTHERS THEN
        RETURN QUERY SELECT FALSE::BOOLEAN, SQLERRM::TEXT;
END;
$$;


-- ===================================================================
-- ATOMIC BATTLE LEAVE/CLEANUP FUNCTION
-- ===================================================================
-- Handles leaving a battle result screen atomically.
-- Clears current_battle for the user.
-- ===================================================================
CREATE OR REPLACE FUNCTION leave_battle_atomic(
    user_uuid UUID
)
RETURNS TABLE(success BOOLEAN)
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE profiles
    SET current_battle = NULL
    WHERE id = user_uuid;

    RETURN QUERY SELECT TRUE::BOOLEAN;

EXCEPTION
    WHEN OTHERS THEN
        RETURN QUERY SELECT FALSE::BOOLEAN;
END;
$$;


-- ===================================================================
-- INDEXES FOR PERFORMANCE
-- ===================================================================
-- These indexes improve lookup performance for the atomic functions

CREATE INDEX IF NOT EXISTS idx_battles_status ON battles(status) WHERE status IN ('active', 'pending');
CREATE INDEX IF NOT EXISTS idx_profiles_current_battle ON profiles(current_battle) WHERE current_battle IS NOT NULL;
