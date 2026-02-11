-- ============================================================================
-- ProductivityGO: Full Database Schema (Fresh Install)
-- ============================================================================
-- This single file creates the entire database from scratch.
-- Run this in Supabase SQL Editor for a new project setup.
--
-- Sections:
--   1. Extensions
--   2. Tables (in FK dependency order)
--   3. Back-reference FKs (added after all tables exist)
--   4. Indexes
--   5. RLS Policies
--   6. Functions (helpers first, then dependents)
--   7. Triggers
--   8. Seed Data (monsters)
--
-- Last updated: 2026-02-07
-- ============================================================================


-- ============================================================================
-- 1. EXTENSIONS
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";


-- ============================================================================
-- 2. TABLES
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 2.1 profiles — User data (extends Supabase Auth)
-- ----------------------------------------------------------------------------
CREATE TABLE public.profiles (
    id UUID REFERENCES auth.users NOT NULL PRIMARY KEY,
    username TEXT UNIQUE,
    email TEXT,
    avatar_emoji TEXT DEFAULT '😀',
    timezone TEXT DEFAULT 'UTC',

    -- XP & leveling
    total_xp_earned INTEGER DEFAULT 0,
    level INT GENERATED ALWAYS AS (
        CASE
            WHEN total_xp_earned < 5000 THEN
                FLOOR(total_xp_earned::NUMERIC / 500) + 1
            WHEN total_xp_earned < 30000 THEN
                FLOOR((total_xp_earned - 5000)::NUMERIC / 1000) + 10
            ELSE
                FLOOR((total_xp_earned - 30000)::NUMERIC / 2000) + 30
        END
    ) STORED,

    -- PVP battle stats
    battle_count INTEGER DEFAULT 0,
    battle_win_count INTEGER DEFAULT 0,
    completed_tasks INTEGER DEFAULT 0,

    -- Adventure mode stats
    adventure_count INTEGER DEFAULT 0,
    monster_defeats INTEGER DEFAULT 0,
    monster_escapes INTEGER DEFAULT 0,
    monster_rating INTEGER DEFAULT 0,
    highest_tier_reached TEXT DEFAULT 'easy',
    total_damage_dealt INTEGER DEFAULT 0,

    -- Monster pool refresh tracking
    monster_pool_refreshes INTEGER DEFAULT 3,
    monster_pool_refresh_set_at TIMESTAMPTZ,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,

    -- Constraints
    CONSTRAINT username_length CHECK (char_length(username) >= 3),
    CONSTRAINT monster_rating_non_negative CHECK (monster_rating >= 0),
    CONSTRAINT highest_tier_valid CHECK (highest_tier_reached IN ('easy', 'medium', 'hard', 'expert', 'boss'))
);

-- ----------------------------------------------------------------------------
-- 2.2 battles — Weekly PVP competitions between two users
-- ----------------------------------------------------------------------------
CREATE TABLE public.battles (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user1_id UUID REFERENCES profiles(id) NOT NULL,
    user2_id UUID REFERENCES profiles(id) NOT NULL,
    winner_id UUID REFERENCES profiles(id),

    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'active', 'completed')),
    duration INTEGER DEFAULT 5,
    current_round INTEGER DEFAULT 0,

    start_date DATE NOT NULL,
    end_date DATE NOT NULL,

    -- Break feature
    break_days_used INTEGER DEFAULT 0,
    max_break_days INTEGER DEFAULT 2,
    is_on_break BOOLEAN DEFAULT false,
    break_end_date DATE,
    break_requested_by UUID REFERENCES profiles(id),
    break_request_expires_at TIMESTAMPTZ,

    -- Completion tracking (idempotency)
    completed_at TIMESTAMPTZ,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- ----------------------------------------------------------------------------
-- 2.3 monsters — Read-only reference data for Adventure Mode
-- ----------------------------------------------------------------------------
CREATE TABLE public.monsters (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    name TEXT NOT NULL,
    emoji TEXT NOT NULL DEFAULT '👹',
    tier TEXT NOT NULL CHECK (tier IN ('easy', 'medium', 'hard', 'expert', 'boss')),
    base_hp INTEGER NOT NULL,
    description TEXT,
    monster_type TEXT
        CHECK (monster_type IN ('sloth','chaos','fog','burnout','stagnation','shadow','titan')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

COMMENT ON TABLE monsters IS 'Monster presets for Adventure Mode single-player gameplay';
COMMENT ON COLUMN monsters.tier IS 'Difficulty tier: easy, medium, hard, expert, boss';
COMMENT ON COLUMN monsters.base_hp IS 'Base HP for this monster. Copied to adventure at creation.';
COMMENT ON COLUMN monsters.monster_type IS 'Elemental type: sloth, chaos, fog, burnout, stagnation, shadow, titan';

-- ----------------------------------------------------------------------------
-- 2.3.1 type_effectiveness — Type multiplier reference table
-- ----------------------------------------------------------------------------
CREATE TABLE public.type_effectiveness (
    monster_type TEXT NOT NULL,
    task_category TEXT NOT NULL,
    multiplier NUMERIC(2,1) NOT NULL CHECK (multiplier IN (0.5, 1.0, 1.5)),
    PRIMARY KEY (monster_type, task_category)
);

COMMENT ON TABLE type_effectiveness IS 'Type effectiveness multipliers for adventure mode combat';
COMMENT ON COLUMN type_effectiveness.multiplier IS '0.5 = resisted, 1.0 = neutral, 1.5 = super effective';

-- ----------------------------------------------------------------------------
-- 2.3.2 type_discoveries — User discovery progress
-- ----------------------------------------------------------------------------
CREATE TABLE public.type_discoveries (
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
-- 2.4 adventures — Single-player monster battles
-- ----------------------------------------------------------------------------
CREATE TABLE public.adventures (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES profiles(id) NOT NULL,
    monster_id UUID REFERENCES monsters(id) NOT NULL,

    -- Duration and timing
    duration INTEGER NOT NULL CHECK (duration BETWEEN 3 AND 7),
    start_date DATE NOT NULL,
    deadline DATE NOT NULL,

    -- Monster state (copied from monster at creation)
    monster_max_hp INTEGER NOT NULL,
    monster_current_hp INTEGER NOT NULL,

    -- Adventure state
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'completed', 'escaped')),
    current_round INTEGER DEFAULT 0,
    total_damage_dealt INTEGER DEFAULT 0,
    xp_earned INTEGER DEFAULT 0,

    -- Break tracking
    break_days_used INTEGER DEFAULT 0,
    max_break_days INTEGER DEFAULT 2,
    is_on_break BOOLEAN DEFAULT false,
    break_end_date DATE,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    completed_at TIMESTAMPTZ
);

COMMENT ON TABLE adventures IS 'User adventures (single-player monster battles) in Adventure Mode';
COMMENT ON COLUMN adventures.status IS 'Adventure status: active, completed (victory), escaped (deadline passed or abandoned)';

-- ----------------------------------------------------------------------------
-- 2.5 daily_entries — Daily progress per user per battle/adventure
-- ----------------------------------------------------------------------------
CREATE TABLE public.daily_entries (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES profiles(id) NOT NULL,
    battle_id UUID REFERENCES battles(id),
    adventure_id UUID REFERENCES adventures(id),
    date DATE NOT NULL,
    is_locked BOOLEAN DEFAULT false,
    daily_xp INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,

    -- Exactly one of battle_id OR adventure_id must be set
    CONSTRAINT daily_entry_game_mode_check CHECK (
        (battle_id IS NOT NULL AND adventure_id IS NULL) OR
        (battle_id IS NULL AND adventure_id IS NOT NULL)
    )
);

-- Partial unique indexes (replaces old unique constraint)
CREATE UNIQUE INDEX daily_entries_unique_pvp
    ON daily_entries (user_id, date)
    WHERE battle_id IS NOT NULL;

CREATE UNIQUE INDEX daily_entries_unique_adventure
    ON daily_entries (user_id, date)
    WHERE adventure_id IS NOT NULL;

COMMENT ON COLUMN daily_entries.adventure_id IS 'References the adventure this entry belongs to (mutually exclusive with battle_id)';
COMMENT ON CONSTRAINT daily_entry_game_mode_check ON daily_entries IS 'Ensures each entry belongs to exactly one game mode: battle (PVP) or adventure (PVE)';

-- ----------------------------------------------------------------------------
-- 2.6 tasks — Individual tasks within daily entries
-- ----------------------------------------------------------------------------
CREATE TABLE public.tasks (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    daily_entry_id UUID REFERENCES daily_entries(id) ON DELETE CASCADE NOT NULL,
    content TEXT NOT NULL,
    is_optional BOOLEAN DEFAULT false,
    is_completed BOOLEAN DEFAULT false,
    proof_url TEXT,
    category TEXT DEFAULT 'errand'
        CHECK (category IN ('errand','focus','physical','creative','social','wellness','organization')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- ----------------------------------------------------------------------------
-- 2.7 follows — Social follow/unfollow system
-- ----------------------------------------------------------------------------
CREATE TABLE public.follows (
    follower_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
    following_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (follower_id, following_id)
);


-- ============================================================================
-- 3. BACK-REFERENCE FOREIGN KEYS
-- ============================================================================
-- Added after all tables exist to avoid circular FK issues.

-- Current active battle for a user
ALTER TABLE profiles ADD COLUMN current_battle UUID REFERENCES battles(id);

-- Current active adventure for a user
ALTER TABLE profiles ADD COLUMN current_adventure UUID REFERENCES adventures(id);


-- ============================================================================
-- 4. INDEXES
-- ============================================================================

-- Profiles
CREATE INDEX IF NOT EXISTS idx_profiles_username ON profiles(username);
CREATE INDEX IF NOT EXISTS idx_profiles_email ON profiles(email);
CREATE INDEX IF NOT EXISTS idx_profiles_current_battle ON profiles(current_battle) WHERE current_battle IS NOT NULL;

-- Battles
CREATE INDEX IF NOT EXISTS idx_battles_user1 ON battles(user1_id);
CREATE INDEX IF NOT EXISTS idx_battles_user2 ON battles(user2_id);
CREATE INDEX IF NOT EXISTS idx_battles_status ON battles(status);
CREATE INDEX IF NOT EXISTS idx_battles_start_date ON battles(start_date);
CREATE INDEX IF NOT EXISTS idx_battles_end_date ON battles(end_date);
CREATE INDEX IF NOT EXISTS idx_battles_user1_status ON battles(user1_id, status);
CREATE INDEX IF NOT EXISTS idx_battles_user2_status ON battles(user2_id, status);
CREATE INDEX IF NOT EXISTS idx_battles_composite ON battles(user1_id, user2_id, status, end_date DESC);
CREATE INDEX IF NOT EXISTS idx_battles_completed_at ON battles(completed_at);

-- Monsters
CREATE INDEX IF NOT EXISTS idx_monsters_tier ON monsters(tier);

-- Type discoveries
CREATE INDEX IF NOT EXISTS idx_type_discoveries_user_monster ON type_discoveries(user_id, monster_type);

-- Adventures
CREATE INDEX IF NOT EXISTS idx_adventures_user_id ON adventures(user_id);
CREATE INDEX IF NOT EXISTS idx_adventures_status ON adventures(status);
CREATE INDEX IF NOT EXISTS idx_adventures_user_status ON adventures(user_id, status);
CREATE INDEX IF NOT EXISTS idx_adventures_deadline ON adventures(deadline);

-- Daily entries
CREATE INDEX IF NOT EXISTS idx_daily_entries_user_date ON daily_entries(user_id, date);
CREATE INDEX IF NOT EXISTS idx_daily_entries_adventure_id ON daily_entries(adventure_id) WHERE adventure_id IS NOT NULL;

-- Tasks
CREATE INDEX IF NOT EXISTS idx_tasks_daily_entry_id ON tasks(daily_entry_id);

-- Follows
CREATE INDEX IF NOT EXISTS idx_follows_following ON follows(following_id);
CREATE INDEX IF NOT EXISTS idx_follows_created_at ON follows(created_at);


-- ============================================================================
-- 5. ROW LEVEL SECURITY (RLS) POLICIES
-- ============================================================================

-- --- Profiles ---
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Public profiles are viewable by everyone."
    ON profiles FOR SELECT USING (true);

CREATE POLICY "Users can insert their own profile."
    ON profiles FOR INSERT WITH CHECK (auth.uid() = id);

CREATE POLICY "Users can update own profile."
    ON profiles FOR UPDATE USING (auth.uid() = id);

-- --- Battles ---
ALTER TABLE battles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their battles"
    ON battles FOR SELECT
    USING (auth.uid() = user1_id OR auth.uid() = user2_id);

CREATE POLICY "Users can create battles"
    ON battles FOR INSERT
    WITH CHECK (auth.uid() = user1_id);

CREATE POLICY "Battle participants can update"
    ON battles FOR UPDATE
    USING (auth.uid() = user1_id OR auth.uid() = user2_id);

-- --- Monsters ---
ALTER TABLE monsters ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Monsters are viewable by everyone"
    ON monsters FOR SELECT USING (true);

-- --- Adventures ---
ALTER TABLE adventures ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own adventures"
    ON adventures FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own adventures"
    ON adventures FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own adventures"
    ON adventures FOR UPDATE USING (auth.uid() = user_id);

-- --- Daily Entries ---
ALTER TABLE daily_entries ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view daily entries for their battles and adventures."
    ON daily_entries FOR SELECT
    USING (
        auth.uid() = user_id OR
        EXISTS (
            SELECT 1 FROM battles
            WHERE battles.id = daily_entries.battle_id
            AND (battles.user1_id = auth.uid() OR battles.user2_id = auth.uid())
        )
    );

CREATE POLICY "Users can insert their daily entries"
    ON daily_entries FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their daily entries"
    ON daily_entries FOR UPDATE
    USING (auth.uid() = user_id);

-- --- Tasks (item 9.1: supports both battle and adventure tasks) ---
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their tasks"
    ON tasks FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM daily_entries de
            WHERE de.id = tasks.daily_entry_id
            AND (
                -- Battle tasks: user is in the battle
                EXISTS (SELECT 1 FROM battles b
                        WHERE b.id = de.battle_id
                        AND (b.user1_id = auth.uid() OR b.user2_id = auth.uid()))
                OR
                -- Adventure tasks: user owns the entry
                (de.adventure_id IS NOT NULL AND de.user_id = auth.uid())
            )
        )
    );

CREATE POLICY "Users can insert tasks"
    ON tasks FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM daily_entries de
            WHERE de.id = tasks.daily_entry_id AND de.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can update their tasks"
    ON tasks FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 FROM daily_entries de
            WHERE de.id = tasks.daily_entry_id AND de.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can delete their tasks"
    ON tasks FOR DELETE
    USING (
        EXISTS (
            SELECT 1 FROM daily_entries de
            WHERE de.id = tasks.daily_entry_id AND de.user_id = auth.uid()
        )
    );

-- --- Follows ---
ALTER TABLE follows ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Public follows access"
    ON follows FOR SELECT USING (true);

CREATE POLICY "Users can follow"
    ON follows FOR INSERT WITH CHECK (auth.uid() = follower_id);

CREATE POLICY "Users can unfollow"
    ON follows FOR DELETE USING (auth.uid() = follower_id);

-- --- Type Effectiveness ---
ALTER TABLE type_effectiveness ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Type effectiveness is viewable by everyone"
    ON type_effectiveness FOR SELECT USING (true);

-- --- Type Discoveries ---
ALTER TABLE type_discoveries ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own discoveries"
    ON type_discoveries FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own discoveries"
    ON type_discoveries FOR INSERT WITH CHECK (auth.uid() = user_id);


-- ============================================================================
-- 6. FUNCTIONS
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 6.1 get_tier_multiplier — Helper: tier -> XP multiplier
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION get_tier_multiplier(tier TEXT)
RETURNS FLOAT AS $$
BEGIN
    RETURN CASE tier
        WHEN 'easy' THEN 1.0
        WHEN 'medium' THEN 1.2
        WHEN 'hard' THEN 1.5
        WHEN 'expert' THEN 2.0
        WHEN 'boss' THEN 3.0
        ELSE 1.0
    END;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- ----------------------------------------------------------------------------
-- 6.2 get_unlocked_tiers — Helper: rating -> unlocked tier names
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

-- ----------------------------------------------------------------------------
-- 6.3 calculate_daily_round — Process one PVP round
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION calculate_daily_round(
    battle_uuid UUID,
    round_date DATE
)
RETURNS TABLE(user1_xp INT, user2_xp INT, winner_id UUID)
LANGUAGE plpgsql
AS $$
DECLARE
    v_user1_id UUID;
    v_user2_id UUID;
    v_quota INT;
    v_user1_xp INT;
    v_user2_xp INT;
    v_winner_id UUID;
BEGIN
    -- Get battle users with row lock
    SELECT user1_id, user2_id INTO v_user1_id, v_user2_id
    FROM battles
    WHERE id = battle_uuid
    FOR UPDATE;

    -- Calculate quota for this date
    v_quota := (('x' || substring(md5(round_date::text), 1, 8))::bit(32)::int % 3) + 3;

    -- Calculate XP for user1
    SELECT COALESCE(
        (COUNT(*) FILTER (WHERE NOT is_optional AND is_completed)::DECIMAL / v_quota * 100)
        + (COUNT(*) FILTER (WHERE is_optional AND is_completed) * 10),
        0
    )::INT INTO v_user1_xp
    FROM tasks t
    JOIN daily_entries de ON de.id = t.daily_entry_id
    WHERE de.user_id = v_user1_id AND de.date = round_date;

    -- Calculate XP for user2
    SELECT COALESCE(
        (COUNT(*) FILTER (WHERE NOT is_optional AND is_completed)::DECIMAL / v_quota * 100)
        + (COUNT(*) FILTER (WHERE is_optional AND is_completed) * 10),
        0
    )::INT INTO v_user2_xp
    FROM tasks t
    JOIN daily_entries de ON de.id = t.daily_entry_id
    WHERE de.user_id = v_user2_id AND de.date = round_date;

    -- Determine winner
    IF v_user1_xp > v_user2_xp THEN
        v_winner_id := v_user1_id;
    ELSIF v_user2_xp > v_user1_xp THEN
        v_winner_id := v_user2_id;
    ELSE
        v_winner_id := NULL; -- Draw
    END IF;

    -- Update daily_entries with XP
    UPDATE daily_entries SET daily_xp = v_user1_xp WHERE user_id = v_user1_id AND date = round_date;
    UPDATE daily_entries SET daily_xp = v_user2_xp WHERE user_id = v_user2_id AND date = round_date;

    RETURN QUERY SELECT v_user1_xp, v_user2_xp, v_winner_id;

EXCEPTION
    WHEN OTHERS THEN
        RAISE EXCEPTION 'calculate_daily_round failed for battle % on date %: %',
            battle_uuid, round_date, SQLERRM;
END;
$$;

-- ----------------------------------------------------------------------------
-- 6.4 complete_battle — Finalize a PVP battle
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION complete_battle(
    battle_uuid UUID
)
RETURNS TABLE(winner_id UUID, user1_total_xp INT, user2_total_xp INT, already_completed BOOLEAN)
LANGUAGE plpgsql
AS $$
DECLARE
    v_user1_id UUID;
    v_user2_id UUID;
    v_user1_total_xp INT;
    v_user2_total_xp INT;
    v_winner_id UUID;
    v_start_date DATE;
    v_end_date DATE;
    v_current_status TEXT;
BEGIN
    -- Get current battle details with row lock
    SELECT status, winner_id, user1_id, user2_id, start_date, end_date
    INTO v_current_status, v_winner_id, v_user1_id, v_user2_id, v_start_date, v_end_date
    FROM battles
    WHERE id = battle_uuid
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Battle not found';
    END IF;

    -- Idempotency: already completed
    IF v_current_status = 'completed' THEN
        SELECT COALESCE(SUM(daily_xp), 0)::INT INTO v_user1_total_xp
        FROM daily_entries
        WHERE user_id = v_user1_id AND date BETWEEN v_start_date AND v_end_date;

        SELECT COALESCE(SUM(daily_xp), 0)::INT INTO v_user2_total_xp
        FROM daily_entries
        WHERE user_id = v_user2_id AND date BETWEEN v_start_date AND v_end_date;

        RETURN QUERY SELECT v_winner_id, v_user1_total_xp, v_user2_total_xp, TRUE::BOOLEAN;
        RETURN;
    END IF;

    -- Sum total XP across all days
    SELECT COALESCE(SUM(daily_xp), 0)::INT INTO v_user1_total_xp
    FROM daily_entries
    WHERE user_id = v_user1_id AND date BETWEEN v_start_date AND v_end_date;

    SELECT COALESCE(SUM(daily_xp), 0)::INT INTO v_user2_total_xp
    FROM daily_entries
    WHERE user_id = v_user2_id AND date BETWEEN v_start_date AND v_end_date;

    -- Determine overall winner
    IF v_user1_total_xp > v_user2_total_xp THEN
        v_winner_id := v_user1_id;
    ELSIF v_user2_total_xp > v_user1_total_xp THEN
        v_winner_id := v_user2_id;
    ELSE
        v_winner_id := NULL; -- Draw
    END IF;

    -- Update battle_win_count
    IF v_winner_id IS NOT NULL THEN
        UPDATE profiles SET battle_win_count = battle_win_count + 1 WHERE id = v_winner_id;
    END IF;

    -- Update total_xp_earned for both
    UPDATE profiles SET total_xp_earned = total_xp_earned + v_user1_total_xp WHERE id = v_user1_id;
    UPDATE profiles SET total_xp_earned = total_xp_earned + v_user2_total_xp WHERE id = v_user2_id;

    -- Increment battle_count for both
    UPDATE profiles SET battle_count = battle_count + 1 WHERE id IN (v_user1_id, v_user2_id);

    -- Mark battle complete with timestamp
    UPDATE battles
    SET status = 'completed',
        winner_id = v_winner_id,
        completed_at = NOW()
    WHERE id = battle_uuid;

    -- Clean up daily_entries (tasks auto-deleted via CASCADE)
    DELETE FROM daily_entries WHERE battle_id = battle_uuid;

    RETURN QUERY SELECT v_winner_id, v_user1_total_xp, v_user2_total_xp, FALSE::BOOLEAN;

EXCEPTION
    WHEN OTHERS THEN
        RAISE EXCEPTION 'complete_battle failed for battle %: %', battle_uuid, SQLERRM;
END;
$$;

-- ----------------------------------------------------------------------------
-- 6.5 forfeit_battle_atomic — Atomic battle forfeiture
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION forfeit_battle_atomic(
    battle_uuid UUID,
    forfeiting_user UUID
)
RETURNS TABLE(winner_id UUID, already_completed BOOLEAN)
LANGUAGE plpgsql
AS $$
DECLARE
    v_user1_id UUID;
    v_user2_id UUID;
    v_winner_id UUID;
    v_current_status TEXT;
    v_loser_id UUID;
    v_forfeiting_is_user1 BOOLEAN;
BEGIN
    SELECT status, user1_id, user2_id
    INTO v_current_status, v_user1_id, v_user2_id
    FROM battles
    WHERE id = battle_uuid
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Battle not found';
    END IF;

    IF v_current_status = 'completed' THEN
        SELECT winner_id INTO v_winner_id FROM battles WHERE id = battle_uuid;
        RETURN QUERY SELECT v_winner_id, TRUE::BOOLEAN;
        RETURN;
    END IF;

    IF v_current_status != 'active' THEN
        RAISE EXCEPTION 'Can only forfeit active battles, current status: %', v_current_status;
    END IF;

    IF forfeiting_user != v_user1_id AND forfeiting_user != v_user2_id THEN
        RAISE EXCEPTION 'User is not a participant in this battle';
    END IF;

    v_forfeiting_is_user1 := (forfeiting_user = v_user1_id);
    IF v_forfeiting_is_user1 THEN
        v_winner_id := v_user2_id;
        v_loser_id := v_user1_id;
    ELSE
        v_winner_id := v_user1_id;
        v_loser_id := v_user2_id;
    END IF;

    UPDATE battles
    SET status = 'completed',
        winner_id = v_winner_id,
        end_date = CURRENT_DATE,
        completed_at = NOW()
    WHERE id = battle_uuid;

    UPDATE profiles
    SET battle_win_count = battle_win_count + 1,
        battle_count = battle_count + 1
    WHERE id = v_winner_id;

    UPDATE profiles
    SET battle_count = battle_count + 1
    WHERE id = v_loser_id;

    RETURN QUERY SELECT v_winner_id, FALSE::BOOLEAN;

EXCEPTION
    WHEN OTHERS THEN
        RAISE;
END;
$$;

-- ----------------------------------------------------------------------------
-- 6.6 accept_battle_atomic — Atomic battle acceptance
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION accept_battle_atomic(
    battle_uuid UUID,
    accepting_user UUID
)
RETURNS TABLE(success BOOLEAN, error_message TEXT)
LANGUAGE plpgsql
AS $$
DECLARE
    v_user1_id UUID;
    v_user2_id UUID;
    v_current_status TEXT;
BEGIN
    SELECT status, user1_id, user2_id
    INTO v_current_status, v_user1_id, v_user2_id
    FROM battles
    WHERE id = battle_uuid
    FOR UPDATE;

    IF NOT FOUND THEN
        RETURN QUERY SELECT FALSE::BOOLEAN, 'Battle not found'::TEXT;
        RETURN;
    END IF;

    IF accepting_user != v_user2_id THEN
        RETURN QUERY SELECT FALSE::BOOLEAN, 'Not your invite to accept'::TEXT;
        RETURN;
    END IF;

    IF v_current_status != 'pending' THEN
        RETURN QUERY SELECT FALSE::BOOLEAN, 'Invite not pending (status: ' || v_current_status || ')'::TEXT;
        RETURN;
    END IF;

    UPDATE battles SET status = 'active' WHERE id = battle_uuid;

    UPDATE profiles SET current_battle = battle_uuid WHERE id = v_user1_id;
    UPDATE profiles SET current_battle = battle_uuid WHERE id = v_user2_id;

    RETURN QUERY SELECT TRUE::BOOLEAN, NULL::TEXT;

EXCEPTION
    WHEN OTHERS THEN
        RETURN QUERY SELECT FALSE::BOOLEAN, SQLERRM::TEXT;
END;
$$;

-- ----------------------------------------------------------------------------
-- 6.7 leave_battle_atomic — Clear current_battle for a user
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION leave_battle_atomic(
    user_uuid UUID
)
RETURNS TABLE(success BOOLEAN)
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE profiles SET current_battle = NULL WHERE id = user_uuid;
    RETURN QUERY SELECT TRUE::BOOLEAN;

EXCEPTION
    WHEN OTHERS THEN
        RETURN QUERY SELECT FALSE::BOOLEAN;
END;
$$;

-- ----------------------------------------------------------------------------
-- 6.8 calculate_adventure_round — Process one PVE round
-- ----------------------------------------------------------------------------
-- Updated for Phase 3: Category-based damage calculation
-- Each task calculates its own damage with type multiplier, then summed
CREATE OR REPLACE FUNCTION calculate_adventure_round(
    adventure_uuid UUID,
    round_date DATE
)
RETURNS TABLE (damage INT, new_hp INT)
LANGUAGE plpgsql
AS $$
DECLARE
    v_adventure RECORD;
    v_entry_id UUID;
    v_monster_type TEXT;
    v_mandatory_total INT;
    v_task_record RECORD;
    v_task_base_damage NUMERIC;
    v_multiplier NUMERIC;
    v_effectiveness TEXT;
    v_total_damage NUMERIC := 0;
    v_damage INT;
    v_new_hp INT;
BEGIN
    -- Get monster type first
    SELECT m.monster_type INTO v_monster_type
    FROM monsters m
    JOIN adventures a ON a.monster_id = m.id
    WHERE a.id = adventure_uuid;

    -- Get adventure with row lock
    SELECT * INTO v_adventure
    FROM adventures
    WHERE id = adventure_uuid
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Adventure not found: %', adventure_uuid;
    END IF;

    -- Handle break status
    IF v_adventure.is_on_break THEN
        IF round_date >= v_adventure.break_end_date THEN
            UPDATE adventures
            SET is_on_break = false, break_end_date = NULL
            WHERE id = adventure_uuid;
        ELSE
            RETURN QUERY SELECT 0, v_adventure.monster_current_hp;
            RETURN;
        END IF;
    END IF;

    -- Get daily entry for this date
    SELECT id INTO v_entry_id
    FROM daily_entries
    WHERE adventure_id = adventure_uuid AND date = round_date;

    IF v_entry_id IS NULL THEN
        RETURN QUERY SELECT 0, v_adventure.monster_current_hp;
        RETURN;
    END IF;

    -- Count total mandatory tasks (for base damage calculation)
    SELECT COUNT(*) FILTER (WHERE NOT is_optional)
    INTO v_mandatory_total
    FROM tasks
    WHERE daily_entry_id = v_entry_id;

    -- Loop through each COMPLETED task and calculate damage individually
    FOR v_task_record IN
        SELECT t.id, t.category, t.is_optional, t.is_completed
        FROM tasks t
        WHERE t.daily_entry_id = v_entry_id AND t.is_completed = true
    LOOP
        -- Calculate base damage for this task
        IF v_task_record.is_optional THEN
            v_task_base_damage := 10;
        ELSE
            -- Avoid division by zero
            IF v_mandatory_total > 0 THEN
                v_task_base_damage := 100::NUMERIC / v_mandatory_total;
            ELSE
                v_task_base_damage := 0;
            END IF;
        END IF;

        -- Get type multiplier from type_effectiveness table
        -- NULL category or missing entry defaults to 1.0 (neutral)
        SELECT COALESCE(te.multiplier, 1.0)
        INTO v_multiplier
        FROM type_effectiveness te
        WHERE te.monster_type = v_monster_type
          AND te.task_category = v_task_record.category;

        -- Accumulate damage
        v_total_damage := v_total_damage + (v_task_base_damage * v_multiplier);

        -- Determine effectiveness for discovery recording
        IF v_multiplier >= 1.5 THEN
            v_effectiveness := 'super_effective';
        ELSIF v_multiplier <= 0.5 THEN
            v_effectiveness := 'resisted';
        ELSE
            v_effectiveness := 'neutral';
        END IF;

        -- Record discovery (idempotent via ON CONFLICT)
        -- Only record if we have a valid category
        IF v_task_record.category IS NOT NULL THEN
            INSERT INTO type_discoveries (user_id, monster_type, task_category, effectiveness, discovered_at)
            VALUES (v_adventure.user_id, v_monster_type, v_task_record.category, v_effectiveness, now())
            ON CONFLICT (user_id, monster_type, task_category) DO NOTHING;
        END IF;
    END LOOP;

    -- Finalize damage: floor and cap at 180 (raised from 120 for SE bonus)
    v_damage := LEAST(FLOOR(v_total_damage), 180)::INT;

    -- Apply damage (floor at 0)
    v_new_hp := GREATEST(v_adventure.monster_current_hp - v_damage, 0);

    -- Update adventure
    UPDATE adventures
    SET monster_current_hp = v_new_hp,
        total_damage_dealt = total_damage_dealt + v_damage,
        current_round = current_round + 1
    WHERE id = adventure_uuid;

    -- Store damage in daily entry
    UPDATE daily_entries SET daily_xp = v_damage WHERE id = v_entry_id;

    RETURN QUERY SELECT v_damage, v_new_hp;

EXCEPTION
    WHEN OTHERS THEN
        RAISE EXCEPTION 'calculate_adventure_round failed for adventure % on date %: %',
            adventure_uuid, round_date, SQLERRM;
END;
$$;

-- ----------------------------------------------------------------------------
-- 6.9 complete_adventure — Finalize an adventure (victory or escape)
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION complete_adventure(
    adventure_uuid UUID
)
RETURNS TABLE (
    status TEXT,
    is_victory BOOLEAN,
    xp_earned INT,
    already_completed BOOLEAN
) AS $$
DECLARE
    v_adv_id UUID;
    v_user_id UUID;
    v_adv_status TEXT;
    v_adv_xp INT;
    v_current_hp INT;
    v_total_damage INT;
    v_is_victory BOOLEAN;
    v_final_xp INT;
    v_multiplier FLOAT;
    v_tier TEXT;
    v_current_highest TEXT;
    v_new_highest TEXT;
BEGIN
    -- Get adventure with monster tier (row lock)
    SELECT
        a.id, a.user_id, a.status, a.xp_earned, a.monster_current_hp,
        a.total_damage_dealt, m.tier
    INTO v_adv_id, v_user_id, v_adv_status, v_adv_xp, v_current_hp,
         v_total_damage, v_tier
    FROM adventures a
    JOIN monsters m ON a.monster_id = m.id
    WHERE a.id = adventure_uuid
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Adventure not found: %', adventure_uuid;
    END IF;

    -- Idempotency
    IF v_adv_status != 'active' THEN
        RETURN QUERY SELECT
            v_adv_status::TEXT,
            v_adv_status = 'completed',
            v_adv_xp::INT,
            TRUE::BOOLEAN;
        RETURN;
    END IF;

    v_is_victory := v_current_hp <= 0;
    v_multiplier := get_tier_multiplier(v_tier);
    v_final_xp := (v_total_damage * v_multiplier *
                   CASE WHEN v_is_victory THEN 1.0 ELSE 0.5 END)::INT;

    -- Update adventure
    UPDATE adventures SET
        status = CASE WHEN v_is_victory THEN 'completed' ELSE 'escaped' END,
        xp_earned = v_final_xp,
        completed_at = NOW()
    WHERE id = v_adv_id;

    -- Get current highest tier
    SELECT COALESCE(highest_tier_reached, 'easy') INTO v_current_highest
    FROM profiles WHERE id = v_user_id;

    -- Calculate new highest tier (only increases on victory)
    IF v_is_victory THEN
        v_new_highest := CASE
            WHEN v_tier = 'boss' THEN 'boss'
            WHEN v_tier = 'expert' AND v_current_highest NOT IN ('boss', 'expert') THEN 'expert'
            WHEN v_tier = 'hard' AND v_current_highest NOT IN ('boss', 'expert', 'hard') THEN 'hard'
            WHEN v_tier = 'medium' AND v_current_highest = 'easy' THEN 'medium'
            ELSE v_current_highest
        END;
    ELSE
        v_new_highest := v_current_highest;
    END IF;

    -- Update user profile stats
    UPDATE profiles SET
        adventure_count = adventure_count + 1,
        monster_defeats = monster_defeats + CASE WHEN v_is_victory THEN 1 ELSE 0 END,
        monster_escapes = monster_escapes + CASE WHEN NOT v_is_victory THEN 1 ELSE 0 END,
        monster_rating = GREATEST(monster_rating + CASE WHEN v_is_victory THEN 1 ELSE -1 END, 0),
        total_xp_earned = total_xp_earned + v_final_xp,
        total_damage_dealt = COALESCE(total_damage_dealt, 0) + v_total_damage,
        current_adventure = NULL,
        highest_tier_reached = v_new_highest
    WHERE id = v_user_id;

    -- Clean up daily_entries (tasks auto-deleted via CASCADE)
    DELETE FROM daily_entries WHERE adventure_id = v_adv_id;

    RETURN QUERY SELECT
        CASE WHEN v_is_victory THEN 'completed' ELSE 'escaped' END::TEXT,
        v_is_victory,
        v_final_xp,
        FALSE::BOOLEAN;

EXCEPTION
    WHEN OTHERS THEN
        RAISE EXCEPTION 'complete_adventure failed for adventure %: %',
            adventure_uuid, SQLERRM;
END;
$$ LANGUAGE plpgsql;

-- ----------------------------------------------------------------------------
-- 6.10 abandon_adventure — Abandon an active adventure early
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION abandon_adventure(
    adventure_uuid UUID,
    abandoning_user UUID
)
RETURNS TABLE (
    status TEXT,
    xp_earned INT
) AS $$
DECLARE
    v_adv_id UUID;
    v_user_id UUID;
    v_adv_status TEXT;
    v_total_damage INT;
    v_multiplier FLOAT;
    v_final_xp INT;
    v_tier TEXT;
BEGIN
    -- Get adventure with tier (row lock)
    SELECT
        a.id, a.user_id, a.status, a.total_damage_dealt, m.tier
    INTO v_adv_id, v_user_id, v_adv_status, v_total_damage, v_tier
    FROM adventures a
    JOIN monsters m ON a.monster_id = m.id
    WHERE a.id = adventure_uuid
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Adventure not found: %', adventure_uuid;
    END IF;

    IF v_user_id != abandoning_user THEN
        RAISE EXCEPTION 'Not your adventure';
    END IF;

    IF v_adv_status != 'active' THEN
        RAISE EXCEPTION 'Adventure is not active (current status: %)', v_adv_status;
    END IF;

    v_multiplier := get_tier_multiplier(v_tier);
    v_final_xp := (v_total_damage * v_multiplier * 0.5)::INT;

    -- Update adventure
    UPDATE adventures SET
        status = 'escaped',
        xp_earned = v_final_xp,
        completed_at = NOW()
    WHERE id = v_adv_id;

    -- Update user profile (counts as escape/loss)
    UPDATE profiles SET
        adventure_count = adventure_count + 1,
        monster_escapes = monster_escapes + 1,
        monster_rating = GREATEST(monster_rating - 1, 0),
        total_xp_earned = total_xp_earned + v_final_xp,
        total_damage_dealt = COALESCE(total_damage_dealt, 0) + v_total_damage,
        current_adventure = NULL
    WHERE id = abandoning_user;

    -- Clean up daily_entries (tasks auto-deleted via CASCADE)
    DELETE FROM daily_entries WHERE adventure_id = v_adv_id;

    RETURN QUERY SELECT 'escaped'::TEXT, v_final_xp;

EXCEPTION
    WHEN OTHERS THEN
        RAISE EXCEPTION 'abandon_adventure failed for adventure %: %',
            adventure_uuid, SQLERRM;
END;
$$ LANGUAGE plpgsql;


-- ============================================================================
-- 7. TRIGGERS
-- ============================================================================

-- Trigger function: auto-update profiles.completed_tasks when tasks change
CREATE OR REPLACE FUNCTION update_completed_tasks()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.is_completed = true AND (TG_OP = 'INSERT' OR OLD.is_completed = false OR OLD.is_completed IS NULL) THEN
        UPDATE profiles SET completed_tasks = completed_tasks + 1
        WHERE id = (SELECT user_id FROM daily_entries WHERE id = NEW.daily_entry_id);

    ELSIF NEW.is_completed = false AND TG_OP = 'UPDATE' AND OLD.is_completed = true THEN
        UPDATE profiles SET completed_tasks = completed_tasks - 1
        WHERE id = (SELECT user_id FROM daily_entries WHERE id = NEW.daily_entry_id);
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_completed_tasks ON tasks;

CREATE TRIGGER trigger_update_completed_tasks
AFTER INSERT OR UPDATE ON tasks
FOR EACH ROW
WHEN (NEW.is_completed IS DISTINCT FROM OLD.is_completed OR OLD.is_completed IS NULL)
EXECUTE FUNCTION update_completed_tasks();


-- ============================================================================
-- 8. SEED DATA — Monsters (42 total across 5 tiers)
-- ============================================================================

DELETE FROM monsters;

INSERT INTO monsters (name, emoji, tier, base_hp, description, monster_type) VALUES
    -- Tier 1: Easy (100-200 HP) - 10 monsters
    ('Lazy Slime', '🟢', 'easy', 100, 'Just five more minutes...', 'sloth'),
    ('Snooze Sprite', '😴', 'easy', 110, 'Whispers "tomorrow is fine"', 'sloth'),
    ('Distraction Rat', '🐀', 'easy', 120, 'Scurries through your focus', 'fog'),
    ('Excuse Imp', '👿', 'easy', 130, 'Always has a reason not to', 'chaos'),
    ('Scroll Goblin', '📱', 'easy', 140, 'Have you seen this meme?', 'fog'),
    ('Couch Potato', '🥔', 'easy', 150, 'The gravity is strong with this one', 'sloth'),
    ('Notification Gremlin', '🔔', 'easy', 160, '*ding* *ding* *ding*', 'fog'),
    ('I''ll Do It Later Larry', '🦥', 'easy', 180, 'Tomorrow''s problem, amirite?', 'stagnation'),
    ('The Snack Siren', '🍕', 'easy', 190, 'Psst... the fridge is calling', 'burnout'),
    ('WiFi Vampire', '📶', 'easy', 200, 'Drains your time, not your blood', 'shadow'),

    -- Tier 2: Medium (200-320 HP) - 10 monsters
    ('Procrastination Goblin', '👺', 'medium', 200, 'There''s still time...', 'sloth'),
    ('Netflix Naga', '🐍', 'medium', 220, 'Just one more episode... or season', 'fog'),
    ('Comfort Zone Troll', '🧌', 'medium', 240, 'Why leave? It''s cozy here', 'stagnation'),
    ('Doom Scroller', '👁️', 'medium', 250, 'Infinite content, zero productivity', 'fog'),
    ('Snack Attack Wolf', '🐺', 'medium', 260, 'Hungry for your time (and snacks)', 'burnout'),
    ('YouTube Rabbit', '🐰', 'medium', 270, 'Recommended for you is its weapon', 'fog'),
    ('Bed Gravity Bear', '🐻', 'medium', 280, 'Makes your bed extra magnetic', 'sloth'),
    ('Reply Guy Wraith', '💬', 'medium', 290, 'Well, actually...', 'shadow'),
    ('Tabocalypse', '🗂️', 'medium', 300, '47 open tabs and counting', 'chaos'),
    ('The Benchwarmer', '🪑', 'medium', 320, 'Just warming up... indefinitely', 'stagnation'),

    -- Tier 3: Hard (320-450 HP) - 10 monsters
    ('Burnout Specter', '👻', 'hard', 320, 'Drains energy you didn''t know you had', 'burnout'),
    ('Impostor Shade', '🎭', 'hard', 340, 'You''re faking it. Everyone knows.', 'shadow'),
    ('FOMO Phantom', '💨', 'hard', 360, 'Everyone''s having fun without you', 'shadow'),
    ('Perfectionism Knight', '⚔️', 'hard', 380, 'Nothing is ever good enough', 'stagnation'),
    ('Analysis Paralysis', '🤯', 'hard', 390, '47 pros/cons lists later...', 'fog'),
    ('Scope Creep', '🦎', 'hard', 400, 'While you''re at it, could you also...', 'chaos'),
    ('Meeting Minotaur', '📅', 'hard', 410, 'This could''ve been an email', 'chaos'),
    ('Decision Fatigue Demon', '🎰', 'hard', 420, 'What should I do? What SHOULD I do??', 'burnout'),
    ('The Comparer', '👀', 'hard', 430, 'Their highlight reel vs your behind-the-scenes', 'shadow'),
    ('Sunk Cost Succubus', '💸', 'hard', 450, 'But I''ve already invested so much...', 'stagnation'),

    -- Tier 4: Expert (450-550 HP) - 7 monsters
    ('Anxiety Dragon', '🐲', 'expert', 450, 'What if everything goes wrong? What if??', 'burnout'),
    ('Overwhelm Hydra', '🐉', 'expert', 470, 'Cut one task, two more appear', 'titan'),
    ('Comparison Demon', '😈', 'expert', 490, 'They''re your age and already...', 'shadow'),
    ('The Infinite Backlog', '📚', 'expert', 500, 'It only grows. It never shrinks.', 'titan'),
    ('Email Avalanche', '📧', 'expert', 510, '1,247 unread and counting', 'chaos'),
    ('Context Switch Chimera', '🦁', 'expert', 530, 'Three heads, three tasks, zero focus', 'fog'),
    ('Imposter Syndrome Supreme', '👑', 'expert', 550, 'The final form of self-doubt', 'shadow'),

    -- Tier 5: Boss (550-700 HP) - 5 monsters
    ('The Void of Inaction', '🕳️', 'boss', 550, 'Where motivation goes to die', 'stagnation'),
    ('Chaos Titan', '🔥', 'boss', 600, 'Master of disorder and delay', 'chaos'),
    ('The Procrastinator King', '👑', 'boss', 650, 'I''ll defeat you... eventually', 'sloth'),
    ('Existential Dread Lord', '🌑', 'boss', 680, 'Does any of this even matter?', 'titan'),
    ('Burnout Phoenix', '🔴', 'boss', 700, 'Rises from the ashes of your motivation', 'burnout');

-- ----------------------------------------------------------------------------
-- Type Effectiveness Seed Data (49 rows: 7 monster types × 7 task categories)
-- ----------------------------------------------------------------------------
-- Multipliers: 0.5 = resisted, 1.0 = neutral, 1.5 = super effective
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
