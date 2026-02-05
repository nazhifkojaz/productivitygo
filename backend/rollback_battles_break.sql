-- ============================================================================
-- Rollback: Remove Break Feature from Battles & Adventure Functions
-- ============================================================================
-- Use this script to rollback Step 1.6 (battles break) and Step 1.7 (functions)
-- ============================================================================

-- Remove break columns from battles table
ALTER TABLE battles
  DROP COLUMN IF EXISTS break_days_used,
  DROP COLUMN IF EXISTS max_break_days,
  DROP COLUMN IF EXISTS is_on_break,
  DROP COLUMN IF EXISTS break_end_date,
  DROP COLUMN IF EXISTS break_requested_by,
  DROP COLUMN IF EXISTS break_request_expires_at;

-- Drop adventure functions
DROP FUNCTION IF EXISTS calculate_adventure_round(UUID, DATE);

-- ============================================================================
-- Rollback Complete
-- ============================================================================
