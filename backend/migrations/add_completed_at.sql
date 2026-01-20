-- Migration: Add completed_at timestamp for battle completion idempotency
-- BUG-001 Fix: Race condition in battle completion
-- This column tracks when a battle was completed to prevent duplicate
-- stat increments from concurrent completion calls.

-- Add completed_at column (nullable for existing battles)
ALTER TABLE battles
ADD COLUMN IF NOT EXISTS completed_at TIMESTAMPTZ;

-- Add index for queries filtering by completion time
CREATE INDEX IF NOT EXISTS idx_battles_completed_at ON battles(completed_at);

-- Add comment for documentation
COMMENT ON COLUMN battles.completed_at IS 'Timestamp when battle was completed. Used for idempotency check to prevent duplicate stat increments from concurrent completion calls.';
