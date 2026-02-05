-- ============================================================================
-- Rollback Script: Adventure Mode Phase 1
-- ============================================================================
-- Use this script to rollback Adventure Mode database changes if needed.
-- WARNING: This will delete all adventure data and cannot be undone.
-- ============================================================================

-- Step 1: Remove adventure constraints and columns from daily_entries
ALTER TABLE daily_entries DROP CONSTRAINT IF EXISTS daily_entry_game_mode_check;
DROP INDEX IF EXISTS idx_daily_entries_adventure_id;
ALTER TABLE daily_entries DROP COLUMN IF EXISTS adventure_id;
ALTER TABLE daily_entries ALTER COLUMN battle_id SET NOT NULL;

-- Restore original RLS policy for daily_entries
DROP POLICY IF EXISTS "Users can view daily entries for their battles and adventures." ON daily_entries;
CREATE POLICY "Users can view daily entries for their battles."
  ON daily_entries FOR SELECT
  USING (
    exists (
      select 1 from battles
      where battles.id = daily_entries.battle_id
      and (battles.user1_id = auth.uid() or battles.user2_id = auth.uid())
    )
  );

-- Step 2: Remove adventure columns from profiles
ALTER TABLE profiles DROP CONSTRAINT IF EXISTS monster_rating_non_negative;
ALTER TABLE profiles DROP CONSTRAINT IF EXISTS highest_tier_valid;
ALTER TABLE profiles DROP COLUMN IF EXISTS current_adventure;
ALTER TABLE profiles DROP COLUMN IF EXISTS adventure_count;
ALTER TABLE profiles DROP COLUMN IF EXISTS adventure_win_count;
ALTER TABLE profiles DROP COLUMN IF EXISTS monster_defeats;
ALTER TABLE profiles DROP COLUMN IF EXISTS monster_escapes;
ALTER TABLE profiles DROP COLUMN IF EXISTS monster_rating;
ALTER TABLE profiles DROP COLUMN IF EXISTS highest_tier_reached;

-- Step 3: Drop adventures table (cascades to daily_entries)
DROP TABLE IF EXISTS adventures CASCADE;

-- Step 4: Drop monsters table
DROP TABLE IF EXISTS monsters CASCADE;

-- ============================================================================
-- Rollback Complete
-- ============================================================================
-- To verify rollback, run:
-- SELECT table_name FROM information_schema.tables WHERE table_name IN ('monsters', 'adventures');
-- Should return 0 rows.
