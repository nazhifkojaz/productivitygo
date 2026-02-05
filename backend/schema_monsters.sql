-- ============================================================================
-- Adventure Mode: Monsters Table
-- ============================================================================
-- This table stores monster presets (name, emoji, tier, HP, description).
-- Monsters are read-only reference data used for Adventure Mode.
-- ============================================================================

-- Create monsters table
CREATE TABLE IF NOT EXISTS monsters (
  id uuid DEFAULT uuid_generate_v4() PRIMARY KEY,
  name text NOT NULL,
  emoji text NOT NULL DEFAULT '👹',
  tier text NOT NULL CHECK (tier IN ('easy', 'medium', 'hard', 'expert', 'boss')),
  base_hp int NOT NULL,
  description text,
  created_at timestamp with time zone DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Add index for tier lookups
CREATE INDEX IF NOT EXISTS idx_monsters_tier ON monsters(tier);

-- Enable RLS
ALTER TABLE monsters ENABLE ROW LEVEL SECURITY;

-- Everyone can read monsters (no auth required for SELECT)
DROP POLICY IF EXISTS "Monsters are viewable by everyone" ON monsters;
CREATE POLICY "Monsters are viewable by everyone"
  ON monsters FOR SELECT
  USING (true);

-- Add comment for documentation
COMMENT ON TABLE monsters IS 'Monster presets for Adventure Mode single-player gameplay';
COMMENT ON COLUMN monsters.tier IS 'Difficulty tier: easy, medium, hard, expert, boss';
COMMENT ON COLUMN monsters.base_hp IS 'Base HP for this monster. Copied to adventure at creation.';
