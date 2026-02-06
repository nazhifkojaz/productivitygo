-- Migration: Cleanup for DB_OPTIMIZATION_AUDIT.md items 1.5, 2.1, 2.2, 3.1
-- Date: 2026-02-06
--
-- Items:
-- 1.5: Remove unused daily_win_count (overall_win_count already removed)
-- 2.1: Remove duplicate adventure_win_count (keep monster_defeats)
-- 2.2: Keep total_damage_dealt (exists in DB, used by functions)
-- 3.1: Convert level to generated column (fixes bug where adventures don't update level)
-- 3.2: Keep monster_rating as-is (acceptable denormalization)

-- 1.5: Remove daily_win_count (never queried, unused)
ALTER TABLE profiles DROP COLUMN IF EXISTS daily_win_count;

-- Note: overall_win_count was already removed or never existed

-- 2.1: Remove adventure_win_count (duplicate of monster_defeats)
ALTER TABLE profiles DROP COLUMN IF EXISTS adventure_win_count;

-- 2.2: total_damage_dealt already exists in DB - no action needed
-- It's used by functions_adventure_completion.sql and functions_adventure.sql

-- 3.1: Convert level to a generated column (PostgreSQL 12+)
-- This fixes the bug where adventure XP doesn't update level
-- Uses piecewise linear progression for better gamification:
--   - Level 1-10:   500 XP per level (early engagement)
--   - Level 11-30:  1000 XP per level (mid-game progression)
--   - Level 31+:    2000 XP per level (long-term goals)
-- First, drop the existing regular column
ALTER TABLE profiles DROP COLUMN IF EXISTS level;

-- Add it back as a generated column with piecewise linear progression
ALTER TABLE profiles ADD COLUMN level INT GENERATED ALWAYS AS (
    CASE
        WHEN total_xp_earned < 5000 THEN
            FLOOR(total_xp_earned::NUMERIC / 500) + 1
        WHEN total_xp_earned < 30000 THEN
            FLOOR((total_xp_earned - 5000)::NUMERIC / 1000) + 10
        ELSE
            FLOOR((total_xp_earned - 30000)::NUMERIC / 2000) + 30
    END
) STORED;

-- 3.2: monster_rating stays as-is (floor-at-zero semantic justifies materializing)
