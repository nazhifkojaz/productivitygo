-- ============================================================================
-- Adventure Mode: Adventures Table
-- ============================================================================
-- This table tracks user adventures (single-player monster battles).
-- Each adventure represents a user's attempt to defeat a monster.
-- ============================================================================

-- Create adventures table
CREATE TABLE IF NOT EXISTS adventures (
  id uuid DEFAULT uuid_generate_v4() PRIMARY KEY,
  user_id uuid REFERENCES profiles(id) NOT NULL,
  monster_id uuid REFERENCES monsters(id) NOT NULL,

  -- Duration and timing
  duration int NOT NULL CHECK (duration BETWEEN 3 AND 7),
  start_date date NOT NULL,
  deadline date NOT NULL,

  -- Monster state (copied from monster at creation for rebalancing safety)
  monster_max_hp int NOT NULL,
  monster_current_hp int NOT NULL,

  -- Adventure state
  status text DEFAULT 'active' CHECK (status IN ('active', 'completed', 'escaped')),
  current_round int DEFAULT 0,
  total_damage_dealt int DEFAULT 0,
  xp_earned int DEFAULT 0,

  -- Break tracking
  break_days_used int DEFAULT 0,
  max_break_days int DEFAULT 2,
  is_on_break boolean DEFAULT false,
  break_end_date date,

  -- Timestamps
  created_at timestamp with time zone DEFAULT timezone('utc'::text, now()) NOT NULL,
  completed_at timestamp with time zone
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_adventures_user_id ON adventures(user_id);
CREATE INDEX IF NOT EXISTS idx_adventures_status ON adventures(status);
CREATE INDEX IF NOT EXISTS idx_adventures_user_status ON adventures(user_id, status);
CREATE INDEX IF NOT EXISTS idx_adventures_deadline ON adventures(deadline);

-- Enable RLS
ALTER TABLE adventures ENABLE ROW LEVEL SECURITY;

-- Users can only see their own adventures
DROP POLICY IF EXISTS "Users can view their own adventures" ON adventures;
CREATE POLICY "Users can view their own adventures"
  ON adventures FOR SELECT
  USING (auth.uid() = user_id);

-- Users can create their own adventures
DROP POLICY IF EXISTS "Users can insert their own adventures" ON adventures;
CREATE POLICY "Users can insert their own adventures"
  ON adventures FOR INSERT
  WITH CHECK (auth.uid() = user_id);

-- Users can update their own adventures
DROP POLICY IF EXISTS "Users can update their own adventures" ON adventures;
CREATE POLICY "Users can update their own adventures"
  ON adventures FOR UPDATE
  USING (auth.uid() = user_id);

-- Add comments for documentation
COMMENT ON TABLE adventures IS 'User adventures (single-player monster battles) in Adventure Mode';
COMMENT ON COLUMN adventures.status IS 'Adventure status: active, completed (victory), escaped (deadline passed or abandoned)';
COMMENT ON COLUMN adventures.break_days_used IS 'Number of break days used by the user (max 2)';
COMMENT ON COLUMN adventures.is_on_break IS 'Whether the adventure is currently paused on a break day';
