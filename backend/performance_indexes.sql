-- Performance Indexes for ProductivityGO
-- These indexes will significantly improve query performance on social features and battles

-- ============================================
-- PROFILES TABLE INDEXES
-- ============================================

-- Index on username for faster username lookups (used in search and navigation)
CREATE INDEX IF NOT EXISTS idx_profiles_username ON profiles(username);

-- Index on email for faster email lookups (used in Battle Station invite lookup)
CREATE INDEX IF NOT EXISTS idx_profiles_email ON profiles(email);

-- NOTE: idx_profiles_avatar_emoji was dropped (item 5.1) - unused, low cardinality

-- ============================================
-- FOLLOWS TABLE INDEXES
-- ============================================

-- NOTE: idx_follows_follower dropped (item 5.3) - covered by PK (follower_id, following_id)
-- NOTE: idx_follows_composite dropped (item 5.2) - duplicate of PK

-- Index on following_id for "who follows me" queries
CREATE INDEX IF NOT EXISTS idx_follows_following ON follows(following_id);

-- Index on created_at for sorting followers by recency
CREATE INDEX IF NOT EXISTS idx_follows_created_at ON follows(created_at);

-- ============================================
-- BATTLES TABLE INDEXES
-- ============================================

-- Index on user1_id for finding battles where user is participant 1
CREATE INDEX IF NOT EXISTS idx_battles_user1 ON battles(user1_id);

-- Index on user2_id for finding battles where user is participant 2
CREATE INDEX IF NOT EXISTS idx_battles_user2 ON battles(user2_id);

-- Index on status for filtering battles by status (pending, active, completed)
CREATE INDEX IF NOT EXISTS idx_battles_status ON battles(status);

-- Index on start_date for sorting and filtering battles by date
CREATE INDEX IF NOT EXISTS idx_battles_start_date ON battles(start_date);

-- Index on end_date for completed battles queries
CREATE INDEX IF NOT EXISTS idx_battles_end_date ON battles(end_date);

-- Composite index for finding active battles for a specific user
CREATE INDEX IF NOT EXISTS idx_battles_user1_status ON battles(user1_id, status);
CREATE INDEX IF NOT EXISTS idx_battles_user2_status ON battles(user2_id, status);

-- Composite index for battle history queries (user + status + date sorting)
CREATE INDEX IF NOT EXISTS idx_battles_composite ON battles(user1_id, user2_id, status, end_date DESC);

-- ============================================
-- DAILY ENTRIES TABLE INDEXES
-- ============================================

-- Composite index on (user_id, date) - most frequent query pattern (item 4.1)
CREATE INDEX IF NOT EXISTS idx_daily_entries_user_date ON daily_entries(user_id, date);

-- Index on adventure_id for adventure completion cleanup (item 4.3)
CREATE INDEX IF NOT EXISTS idx_daily_entries_adventure_id ON daily_entries(adventure_id)
    WHERE adventure_id IS NOT NULL;

-- ============================================
-- TASKS TABLE INDEXES
-- ============================================

-- Index on daily_entry_id foreign key (item 4.4)
CREATE INDEX IF NOT EXISTS idx_tasks_daily_entry_id ON tasks(daily_entry_id);

-- ============================================
-- EXPECTED IMPACT
-- ============================================
-- - Following/Followers queries: 50-80% faster
-- - User search: 60-70% faster
-- - Battle lookups: 40-60% faster
-- - Overall social hub loading: 50% faster
