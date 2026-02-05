-- ============================================================================
-- Rollback: Remove Adventure Mode Completion Functions
-- ============================================================================
-- Use this script to rollback Steps 1.8, 1.9, and 1.10
-- ============================================================================

DROP FUNCTION IF EXISTS complete_adventure(UUID);
DROP FUNCTION IF EXISTS abandon_adventure(UUID, UUID);
DROP FUNCTION IF EXISTS get_unlocked_tiers(INT);

-- ============================================================================
-- Rollback Complete
-- ============================================================================
