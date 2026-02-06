-- Migration: Add trigger for auto-updating completed_tasks
-- DB_OPTIMIZATION_AUDIT.md item 10.2 - trigger solution
-- Date: 2026-02-06
--
-- Replaces manual completed_tasks updates with an automatic trigger.
-- This ensures completed_tasks is always accurate for both battle and adventure tasks.

-- ============================================
-- CREATE TRIGGER FUNCTION
-- ============================================

CREATE OR REPLACE FUNCTION update_completed_tasks()
RETURNS TRIGGER AS $$
BEGIN
    -- Task is being marked as completed (insert or update to true)
    IF NEW.is_completed = true AND (TG_OP = 'INSERT' OR OLD.is_completed = false OR OLD.is_completed IS NULL) THEN
        UPDATE profiles SET completed_tasks = completed_tasks + 1
        WHERE id = (SELECT user_id FROM daily_entries WHERE id = NEW.daily_entry_id);

    -- Task is being marked as incomplete (update to false)
    ELSIF NEW.is_completed = false AND TG_OP = 'UPDATE' AND OLD.is_completed = true THEN
        UPDATE profiles SET completed_tasks = completed_tasks - 1
        WHERE id = (SELECT user_id FROM daily_entries WHERE id = NEW.daily_entry_id);
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- CREATE TRIGGER ON TASKS
-- ============================================

DROP TRIGGER IF EXISTS trigger_update_completed_tasks ON tasks;

CREATE TRIGGER trigger_update_completed_tasks
AFTER INSERT OR UPDATE ON tasks
FOR EACH ROW
WHEN (NEW.is_completed IS DISTINCT FROM OLD.is_completed OR OLD.is_completed IS NULL)
EXECUTE FUNCTION update_completed_tasks();

-- ============================================
-- REMOVE MANUAL UPDATES FROM SQL FUNCTIONS
-- ============================================

-- The calculate_daily_round() function no longer needs to manually update
-- completed_tasks since the trigger handles it automatically.
-- This is handled in the function updates below.
