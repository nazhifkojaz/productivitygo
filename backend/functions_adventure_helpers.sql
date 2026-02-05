-- ============================================================================
-- Adventure Mode Helper Functions
-- ============================================================================
-- Utility functions for Adventure Mode progression logic.
-- Run in Supabase SQL Editor or deploy via deploy_adventure_completion.py
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Function: get_unlocked_tiers
-- ----------------------------------------------------------------------------
-- Returns array of unlocked tier names based on monster rating.
--
-- Parameters:
--   rating INT - Current monster rating (defeats - escapes, floored at 0)
--
-- Returns:
--   TEXT[] - Array of unlocked tier names
--
-- Unlock thresholds:
--   0-1   -> {easy}
--   2-4   -> {easy, medium}
--   5-8   -> {easy, medium, hard}
--   9-13  -> {easy, medium, hard, expert}
--   14+   -> {easy, medium, hard, expert, boss}
-- ----------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION get_unlocked_tiers(rating INT)
RETURNS TEXT[] AS $$
BEGIN
    IF rating >= 14 THEN
        RETURN ARRAY['easy', 'medium', 'hard', 'expert', 'boss'];
    ELSIF rating >= 9 THEN
        RETURN ARRAY['easy', 'medium', 'hard', 'expert'];
    ELSIF rating >= 5 THEN
        RETURN ARRAY['easy', 'medium', 'hard'];
    ELSIF rating >= 2 THEN
        RETURN ARRAY['easy', 'medium'];
    ELSE
        RETURN ARRAY['easy'];
    END IF;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Add comment for documentation
COMMENT ON FUNCTION get_unlocked_tiers IS 'Returns array of unlocked tier names based on monster rating. Rating = defeats - escapes (floored at 0).';
