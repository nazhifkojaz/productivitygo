-- ============================================================================
-- Migration: Add Break Feature to Battles Table
-- ============================================================================
-- Adds break tracking for PVP battles. Both players must agree to take a break.
-- One player requests, the other accepts. Request auto-expires on day change.
-- ============================================================================

ALTER TABLE battles
  ADD COLUMN IF NOT EXISTS break_days_used int DEFAULT 0,
  ADD COLUMN IF NOT EXISTS max_break_days int DEFAULT 2,
  ADD COLUMN IF NOT EXISTS is_on_break boolean DEFAULT false,
  ADD COLUMN IF NOT EXISTS break_end_date date,
  ADD COLUMN IF NOT EXISTS break_requested_by uuid REFERENCES profiles(id),
  ADD COLUMN IF NOT EXISTS break_request_expires_at timestamptz;

-- Add comments for documentation
COMMENT ON COLUMN battles.break_days_used IS 'Number of break days used in this battle (max 2)';
COMMENT ON COLUMN battles.max_break_days IS 'Maximum break days allowed (default 2)';
COMMENT ON COLUMN battles.is_on_break IS 'Whether the battle is currently paused on a break day';
COMMENT ON COLUMN battles.break_end_date IS 'When the current break ends';
COMMENT ON COLUMN battles.break_requested_by IS 'Which player requested the break (user1 or user2)';
COMMENT ON COLUMN battles.break_request_expires_at IS 'When the break request auto-declines (day change for both players)';
