-- ============================================================================
-- Migration: Add Adventure Mode support to daily_entries
-- ============================================================================
-- Allows daily_entries to be associated with either a battle (PVP) or
-- adventure (PVE). Exactly one must be set.
-- ============================================================================

-- Step 1: Add adventure_id column (nullable initially, for backward compatibility)
ALTER TABLE daily_entries
  ADD COLUMN IF NOT EXISTS adventure_id uuid REFERENCES adventures(id);

-- Step 2: Make battle_id nullable (was NOT NULL before)
-- This allows entries to be associated with adventures instead
ALTER TABLE daily_entries
  ALTER COLUMN battle_id DROP NOT NULL;

-- Step 3: Add constraint - exactly one of battle_id OR adventure_id must be set
ALTER TABLE daily_entries
  ADD CONSTRAINT daily_entry_game_mode_check
  CHECK (
    (battle_id IS NOT NULL AND adventure_id IS NULL) OR
    (battle_id IS NULL AND adventure_id IS NOT NULL)
  );

-- Step 4: Add index for adventure lookups
CREATE INDEX IF NOT EXISTS idx_daily_entries_adventure_id ON daily_entries(adventure_id);

-- Step 5: Update RLS policy to include adventure-based entries
DROP POLICY IF EXISTS "Users can view daily entries for their battles." ON daily_entries;
CREATE POLICY "Users can view daily entries for their battles and adventures."
  ON daily_entries FOR SELECT
  USING (
    auth.uid() = user_id OR
    exists (
      select 1 from battles
      where battles.id = daily_entries.battle_id
      and (battles.user1_id = auth.uid() or battles.user2_id = auth.uid())
    )
  );

-- Add comment for documentation
COMMENT ON COLUMN daily_entries.adventure_id IS 'References the adventure this entry belongs to (mutually exclusive with battle_id)';
COMMENT ON CONSTRAINT daily_entry_game_mode_check ON daily_entries IS 'Ensures each entry belongs to exactly one game mode: battle (PVP) or adventure (PVE)';
