-- ============================================================================
-- Migration 001: Add Task Categories and Monster Types
-- ============================================================================
-- This migration adds the elemental combat system to Adventure Mode.
--
-- Changes:
--   1. Add `category` column to `tasks` table
--   2. Add `monster_type` column to `monsters` table
--   3. Create `type_effectiveness` reference table
--   4. Create `type_discoveries` table
--   5. Update existing monsters with their types
--   6. Seed type effectiveness data
--   7. Add RLS policies for new tables
--   8. Add indexes
--
-- Run this in Supabase SQL Editor for production deployment.
-- ============================================================================


-- ----------------------------------------------------------------------------
-- Step 1: Add category column to tasks table
-- ----------------------------------------------------------------------------
ALTER TABLE tasks
    ADD COLUMN category TEXT DEFAULT 'errand'
        CHECK (category IN ('errand','focus','physical','creative','social','wellness','organization'));


-- ----------------------------------------------------------------------------
-- Step 2: Add monster_type column to monsters table (nullable first)
-- ----------------------------------------------------------------------------
ALTER TABLE monsters
    ADD COLUMN monster_type TEXT
        CHECK (monster_type IN ('sloth','chaos','fog','burnout','stagnation','shadow','titan'));


-- ----------------------------------------------------------------------------
-- Step 3: Create type_effectiveness reference table
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.type_effectiveness (
    monster_type TEXT NOT NULL,
    task_category TEXT NOT NULL,
    multiplier NUMERIC(2,1) NOT NULL CHECK (multiplier IN (0.5, 1.0, 1.5)),
    PRIMARY KEY (monster_type, task_category)
);

COMMENT ON TABLE type_effectiveness IS 'Type effectiveness multipliers for adventure mode combat';
COMMENT ON COLUMN type_effectiveness.multiplier IS '0.5 = resisted, 1.0 = neutral, 1.5 = super effective';


-- ----------------------------------------------------------------------------
-- Step 4: Create type_discoveries table
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.type_discoveries (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES profiles(id) ON DELETE CASCADE NOT NULL,
    monster_type TEXT NOT NULL,
    task_category TEXT NOT NULL,
    effectiveness TEXT NOT NULL CHECK (effectiveness IN ('super_effective', 'neutral', 'resisted')),
    discovered_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    UNIQUE (user_id, monster_type, task_category)
);

COMMENT ON TABLE type_discoveries IS 'Tracks which type effectiveness each user has discovered through combat';


-- ----------------------------------------------------------------------------
-- Step 5: Update all 42 monsters with their types
-- ----------------------------------------------------------------------------

-- Easy Tier (10 monsters)
UPDATE monsters SET monster_type = 'sloth' WHERE name IN ('Lazy Slime', 'Snooze Sprite', 'Couch Potato');
UPDATE monsters SET monster_type = 'fog' WHERE name IN ('Distraction Rat', 'Scroll Goblin', 'Notification Gremlin');
UPDATE monsters SET monster_type = 'chaos' WHERE name = 'Excuse Imp';
UPDATE monsters SET monster_type = 'stagnation' WHERE name = 'I''ll Do It Later Larry';
UPDATE monsters SET monster_type = 'burnout' WHERE name = 'The Snack Siren';
UPDATE monsters SET monster_type = 'shadow' WHERE name = 'WiFi Vampire';

-- Medium Tier (10 monsters)
UPDATE monsters SET monster_type = 'sloth' WHERE name IN ('Procrastination Goblin', 'Bed Gravity Bear');
UPDATE monsters SET monster_type = 'fog' WHERE name IN ('Netflix Naga', 'Doom Scroller', 'YouTube Rabbit');
UPDATE monsters SET monster_type = 'stagnation' WHERE name IN ('Comfort Zone Troll', 'The Benchwarmer');
UPDATE monsters SET monster_type = 'burnout' WHERE name = 'Snack Attack Wolf';
UPDATE monsters SET monster_type = 'shadow' WHERE name = 'Reply Guy Wraith';
UPDATE monsters SET monster_type = 'chaos' WHERE name = 'Tabocalypse';

-- Hard Tier (10 monsters)
UPDATE monsters SET monster_type = 'burnout' WHERE name IN ('Burnout Specter', 'Decision Fatigue Demon');
UPDATE monsters SET monster_type = 'shadow' WHERE name IN ('Impostor Shade', 'FOMO Phantom', 'The Comparer');
UPDATE monsters SET monster_type = 'stagnation' WHERE name IN ('Perfectionism Knight', 'Sunk Cost Succubus');
UPDATE monsters SET monster_type = 'fog' WHERE name = 'Analysis Paralysis';
UPDATE monsters SET monster_type = 'chaos' WHERE name IN ('Scope Creep', 'Meeting Minotaur');

-- Expert Tier (7 monsters)
UPDATE monsters SET monster_type = 'burnout' WHERE name = 'Anxiety Dragon';
UPDATE monsters SET monster_type = 'titan' WHERE name IN ('Overwhelm Hydra', 'The Infinite Backlog');
UPDATE monsters SET monster_type = 'shadow' WHERE name IN ('Comparison Demon', 'Imposter Syndrome Supreme');
UPDATE monsters SET monster_type = 'chaos' WHERE name = 'Email Avalanche';
UPDATE monsters SET monster_type = 'fog' WHERE name = 'Context Switch Chimera';

-- Boss Tier (5 monsters)
UPDATE monsters SET monster_type = 'stagnation' WHERE name = 'The Void of Inaction';
UPDATE monsters SET monster_type = 'chaos' WHERE name = 'Chaos Titan';
UPDATE monsters SET monster_type = 'sloth' WHERE name = 'The Procrastinator King';
UPDATE monsters SET monster_type = 'titan' WHERE name = 'Existential Dread Lord';
UPDATE monsters SET monster_type = 'burnout' WHERE name = 'Burnout Phoenix';

-- Now set monster_type to NOT NULL (after all rows have values)
ALTER TABLE monsters ALTER COLUMN monster_type SET NOT NULL;


-- ----------------------------------------------------------------------------
-- Step 6: Seed type effectiveness data (49 rows)
-- ----------------------------------------------------------------------------
-- Clear any existing data first
DELETE FROM type_effectiveness;

INSERT INTO type_effectiveness (monster_type, task_category, multiplier) VALUES
    -- Sloth: weak to Physical, Errand | resistant to Wellness, Social
    ('sloth', 'errand', 1.5),
    ('sloth', 'focus', 1.0),
    ('sloth', 'physical', 1.5),
    ('sloth', 'creative', 1.0),
    ('sloth', 'social', 0.5),
    ('sloth', 'wellness', 0.5),
    ('sloth', 'organization', 1.0),

    -- Chaos: weak to Organization, Errand | resistant to Creative, Focus
    ('chaos', 'errand', 1.5),
    ('chaos', 'focus', 0.5),
    ('chaos', 'physical', 1.0),
    ('chaos', 'creative', 0.5),
    ('chaos', 'social', 1.0),
    ('chaos', 'wellness', 1.0),
    ('chaos', 'organization', 1.5),

    -- Fog: weak to Focus, Organization | resistant to Physical, Errand
    ('fog', 'errand', 0.5),
    ('fog', 'focus', 1.5),
    ('fog', 'physical', 0.5),
    ('fog', 'creative', 1.0),
    ('fog', 'social', 1.0),
    ('fog', 'wellness', 1.0),
    ('fog', 'organization', 1.5),

    -- Burnout: weak to Wellness, Creative | resistant to Focus, Organization
    ('burnout', 'errand', 1.0),
    ('burnout', 'focus', 0.5),
    ('burnout', 'physical', 1.0),
    ('burnout', 'creative', 1.5),
    ('burnout', 'social', 1.0),
    ('burnout', 'wellness', 1.5),
    ('burnout', 'organization', 0.5),

    -- Stagnation: weak to Creative, Social | resistant to Errand, Organization
    ('stagnation', 'errand', 0.5),
    ('stagnation', 'focus', 1.0),
    ('stagnation', 'physical', 1.0),
    ('stagnation', 'creative', 1.5),
    ('stagnation', 'social', 1.5),
    ('stagnation', 'wellness', 1.0),
    ('stagnation', 'organization', 0.5),

    -- Shadow: weak to Social, Wellness | resistant to Physical, Creative
    ('shadow', 'errand', 1.0),
    ('shadow', 'focus', 1.0),
    ('shadow', 'physical', 0.5),
    ('shadow', 'creative', 0.5),
    ('shadow', 'social', 1.5),
    ('shadow', 'wellness', 1.5),
    ('shadow', 'organization', 1.0),

    -- Titan: weak to Focus, Physical | resistant to Social, Wellness
    ('titan', 'errand', 1.0),
    ('titan', 'focus', 1.5),
    ('titan', 'physical', 1.5),
    ('titan', 'creative', 1.0),
    ('titan', 'social', 0.5),
    ('titan', 'wellness', 0.5),
    ('titan', 'organization', 1.0);


-- ----------------------------------------------------------------------------
-- Step 7: Create index for type_discoveries
-- ----------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_type_discoveries_user_monster
    ON type_discoveries(user_id, monster_type);


-- ----------------------------------------------------------------------------
-- Step 8: Add RLS policies for new tables
-- ----------------------------------------------------------------------------

-- Type effectiveness: read-only for all authenticated users
ALTER TABLE type_effectiveness ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Type effectiveness is viewable by everyone"
    ON type_effectiveness FOR SELECT USING (true);

-- Type discoveries: users can see and insert their own
ALTER TABLE type_discoveries ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own discoveries"
    ON type_discoveries FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own discoveries"
    ON type_discoveries FOR INSERT WITH CHECK (auth.uid() = user_id);


-- ----------------------------------------------------------------------------
-- Verification queries (run these to verify the migration)
-- ----------------------------------------------------------------------------

-- Verify tasks has category column
-- SELECT column_name, data_type, column_default
-- FROM information_schema.columns
-- WHERE table_name = 'tasks' AND column_name = 'category';

-- Verify monsters has monster_type column
-- SELECT column_name, data_type, is_nullable
-- FROM information_schema.columns
-- WHERE table_name = 'monsters' AND column_name = 'monster_type';

-- Verify all monsters have a type (should return 0)
-- SELECT COUNT(*) FROM monsters WHERE monster_type IS NULL;

-- Verify type_effectiveness has 49 rows
-- SELECT COUNT(*) FROM type_effectiveness;

-- Verify type distribution
-- SELECT monster_type, COUNT(*) as count, tier
-- FROM monsters
-- GROUP BY monster_type, tier
-- ORDER BY tier, monster_type;
