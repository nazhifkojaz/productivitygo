-- Migration: Remove dead/orphaned columns identified in DB optimization audit
-- Date: 2026-02-06
-- Items: 1.2, 1.3, 1.4 from DB_OPTIMIZATION_AUDIT.md
--
-- Note: 1.1 (profiles.exp) was already removed by schema_cleanup_columns.sql
-- This migration cleans up the remaining dead columns in daily_entries

-- 1.2: Remove daily_entries.score_distribution
-- Reason: Replaced by MD5-based quota formula in calculate_daily_round()
-- Impact: JSONB column that is never read or written
ALTER TABLE daily_entries DROP COLUMN IF EXISTS score_distribution;

-- 1.3: Remove daily_entries.day_winner
-- Reason: Winner is determined in-function and returned, not stored
-- Impact: Boolean column that is never used
ALTER TABLE daily_entries DROP COLUMN IF EXISTS day_winner;

-- 1.4: Remove daily_entries.is_daily_winner
-- Reason: Added by schema_battle_scoring.sql but never used
-- Impact: Redundant with day_winner, both unused
ALTER TABLE daily_entries DROP COLUMN IF EXISTS is_daily_winner;
