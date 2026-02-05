-- ============================================================================
-- Migration: Add Adventure Mode stats to profiles
-- ============================================================================
-- Adds columns to track user progress in Adventure Mode:
-- - Current adventure tracking
-- - Adventure completion stats
-- - Monster progression (defeats, escapes, rating)
-- - Highest tier reached
-- ============================================================================

-- Current session tracking
ALTER TABLE profiles
  ADD COLUMN IF NOT EXISTS current_adventure uuid REFERENCES adventures(id);

-- Adventure stats
ALTER TABLE profiles
  ADD COLUMN IF NOT EXISTS adventure_count int DEFAULT 0,
  ADD COLUMN IF NOT EXISTS adventure_win_count int DEFAULT 0;

-- Monster progression
ALTER TABLE profiles
  ADD COLUMN IF NOT EXISTS monster_defeats int DEFAULT 0,
  ADD COLUMN IF NOT EXISTS monster_escapes int DEFAULT 0,
  ADD COLUMN IF NOT EXISTS monster_rating int DEFAULT 0,
  ADD COLUMN IF NOT EXISTS highest_tier_reached text DEFAULT 'easy';

-- Add check constraint for monster_rating (floor at 0)
-- Drop first to avoid errors on re-run
ALTER TABLE profiles DROP CONSTRAINT IF EXISTS monster_rating_non_negative;
ALTER TABLE profiles
  ADD CONSTRAINT monster_rating_non_negative
  CHECK (monster_rating >= 0);

-- Add check constraint for highest_tier_reached (valid values only)
-- Drop first to avoid errors on re-run
ALTER TABLE profiles DROP CONSTRAINT IF EXISTS highest_tier_valid;
ALTER TABLE profiles
  ADD CONSTRAINT highest_tier_valid
  CHECK (highest_tier_reached IN ('easy', 'medium', 'hard', 'expert', 'boss'));

-- Add comments for documentation
COMMENT ON COLUMN profiles.current_adventure IS 'Currently active adventure (mutually exclusive with current_battle)';
COMMENT ON COLUMN profiles.adventure_count IS 'Total number of adventures completed';
COMMENT ON COLUMN profiles.adventure_win_count IS 'Number of monsters defeated (victories)';
COMMENT ON COLUMN profiles.monster_defeats IS 'Total monsters defeated (same as adventure_win_count)';
COMMENT ON COLUMN profiles.monster_escapes IS 'Total monsters that escaped (losses)';
COMMENT ON COLUMN profiles.monster_rating IS 'Monster Rating = defeats - escapes (floored at 0), determines tier unlock';
COMMENT ON COLUMN profiles.highest_tier_reached IS 'Highest difficulty tier the user has defeated: easy, medium, hard, expert, boss';
