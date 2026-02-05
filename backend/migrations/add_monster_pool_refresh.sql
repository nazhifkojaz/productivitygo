-- ============================================================================
-- Migration: Monster Pool Refresh Tracking (Redis-Free)
-- ============================================================================
-- Adds columns to profiles table to track monster pool refresh counts
-- without requiring Redis. This replaces in-memory refresh tracking.
--
-- Columns:
--   monster_pool_refreshes - Remaining refreshes (default 3)
--   monster_pool_refresh_set_at - Timestamp when pool was last set
--
-- Logic:
--   - Reset to 3 when user first views monsters (if not set today)
--   - Decrement on each refresh
--   - Reset to NULL when adventure starts
-- ============================================================================

-- Add refresh tracking columns
ALTER TABLE profiles
  ADD COLUMN IF NOT EXISTS monster_pool_refreshes INT DEFAULT 3,
  ADD COLUMN IF NOT EXISTS monster_pool_refresh_set_at TIMESTAMPTZ;

-- Add comment for documentation
COMMENT ON COLUMN profiles.monster_pool_refreshes IS 'Remaining monster pool refreshes. Resets to 3 on new adventure session.';
COMMENT ON COLUMN profiles.monster_pool_refresh_set_at IS 'Timestamp when monster pool was last generated. Used to detect new sessions.';
