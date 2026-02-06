"""
Integration tests for Adventure Mode database schema.

These tests verify that:
1. Tables exist with correct columns and constraints
2. RLS policies work correctly
3. Monster data is seeded correctly
4. Constraints prevent invalid data

Run after deploying Adventure Mode SQL migrations.

Usage:
    pytest tests/integration/test_adventure_schema.py -v
"""
import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    from database import get_db_connection, return_db_connection
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False


@pytest.mark.skipif(not DB_AVAILABLE, reason="Database connection not available")
class TestMonstersTable:
    """Tests for the monsters table."""

    def test_table_exists(self):
        """Verify monsters table exists."""
        conn = get_db_connection()
        if not conn:
            pytest.skip("No database connection")
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'monsters'
                );
            """)
            result = cursor.fetchone()
            assert result[0] is True, "Monsters table does not exist"
        finally:
            cursor.close()
            return_db_connection(conn)

    def test_monster_count_by_tier(self):
        """Verify correct number of monsters per tier."""
        conn = get_db_connection()
        if not conn:
            pytest.skip("No database connection")
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT tier, COUNT(*) as count
                FROM monsters
                GROUP BY tier
                ORDER BY tier;
            """)
            results = {tier: count for tier, count in cursor.fetchall()}

            # Expected counts from design doc
            expected = {
                'easy': 10,
                'medium': 10,
                'hard': 10,
                'expert': 7,
                'boss': 5
            }

            for tier, expected_count in expected.items():
                actual = results.get(tier, 0)
                assert actual == expected_count, f"Tier {tier}: expected {expected_count}, got {actual}"
        finally:
            cursor.close()
            return_db_connection(conn)

    def test_monster_hp_ranges(self):
        """Verify monster HP ranges are correct per tier."""
        conn = get_db_connection()
        if not conn:
            pytest.skip("No database connection")
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT tier, MIN(base_hp) as min_hp, MAX(base_hp) as max_hp
                FROM monsters
                GROUP BY tier
                ORDER BY min_hp;
            """)
            results = cursor.fetchall()

            expected_ranges = {
                'easy': (100, 200),
                'medium': (200, 320),
                'hard': (320, 450),
                'expert': (450, 550),
                'boss': (550, 700)
            }

            for tier, min_hp, max_hp in results:
                expected_min, expected_max = expected_ranges[tier]
                assert min_hp == expected_min, f"Tier {tier} min HP: expected {expected_min}, got {min_hp}"
                assert max_hp == expected_max, f"Tier {tier} max HP: expected {expected_max}, got {max_hp}"
        finally:
            cursor.close()
            return_db_connection(conn)

    def test_monster_required_columns(self):
        """Verify monsters table has all required columns."""
        conn = get_db_connection()
        if not conn:
            pytest.skip("No database connection")
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'monsters'
                ORDER BY ordinal_position;
            """)
            columns = {row[0] for row in cursor.fetchall()}

            required_columns = {
                'id', 'name', 'emoji', 'tier', 'base_hp', 'description', 'created_at'
            }
            assert required_columns.issubset(columns), f"Missing columns: {required_columns - columns}"
        finally:
            cursor.close()
            return_db_connection(conn)

    def test_monster_tier_constraint(self):
        """Verify tier constraint only allows valid values."""
        conn = get_db_connection()
        if not conn:
            pytest.skip("No database connection")
        try:
            cursor = conn.cursor()
            # This query should return the check constraint for tier
            cursor.execute("""
                SELECT pg_get_constraintdef(oid)
                FROM pg_constraint
                WHERE conrelid = 'monsters'::regclass
                AND conname LIKE '%tier%';
            """)
            result = cursor.fetchone()
            assert result is not None, "No tier constraint found"
            constraint_def = result[0]
            assert 'easy' in constraint_def, "Tier constraint missing 'easy' value"
            assert 'boss' in constraint_def, "Tier constraint missing 'boss' value"
        finally:
            cursor.close()
            return_db_connection(conn)


@pytest.mark.skipif(not DB_AVAILABLE, reason="Database connection not available")
class TestAdventuresTable:
    """Tests for the adventures table."""

    def test_table_exists(self):
        """Verify adventures table exists."""
        conn = get_db_connection()
        if not conn:
            pytest.skip("No database connection")
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'adventures'
                );
            """)
            result = cursor.fetchone()
            assert result[0] is True, "Adventures table does not exist"
        finally:
            cursor.close()
            return_db_connection(conn)

    def test_adventure_required_columns(self):
        """Verify adventures table has all required columns."""
        conn = get_db_connection()
        if not conn:
            pytest.skip("No database connection")
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'adventures'
                ORDER BY ordinal_position;
            """)
            columns = {row[0] for row in cursor.fetchall()}

            required_columns = {
                'id', 'user_id', 'monster_id', 'duration', 'start_date', 'deadline',
                'monster_max_hp', 'monster_current_hp', 'status', 'current_round',
                'total_damage_dealt', 'xp_earned', 'break_days_used', 'max_break_days',
                'is_on_break', 'break_end_date', 'created_at', 'completed_at'
            }
            assert required_columns.issubset(columns), f"Missing columns: {required_columns - columns}"
        finally:
            cursor.close()
            return_db_connection(conn)

    def test_adventure_status_constraint(self):
        """Verify status constraint only allows valid values."""
        conn = get_db_connection()
        if not conn:
            pytest.skip("No database connection")
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT pg_get_constraintdef(oid)
                FROM pg_constraint
                WHERE conrelid = 'adventures'::regclass
                AND conname LIKE '%status%';
            """)
            result = cursor.fetchone()
            assert result is not None, "No status constraint found"
            constraint_def = result[0]
            assert 'active' in constraint_def, "Status constraint missing 'active' value"
            assert 'completed' in constraint_def, "Status constraint missing 'completed' value"
            assert 'escaped' in constraint_def, "Status constraint missing 'escaped' value"
        finally:
            cursor.close()
            return_db_connection(conn)

    def test_adventure_duration_constraint(self):
        """Verify duration constraint allows 3-7 days only."""
        conn = get_db_connection()
        if not conn:
            pytest.skip("No database connection")
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT pg_get_constraintdef(oid)
                FROM pg_constraint
                WHERE conrelid = 'adventures'::regclass
                AND conname LIKE '%duration%';
            """)
            result = cursor.fetchone()
            assert result is not None, "No duration constraint found"
            constraint_def = result[0]
            assert '3' in constraint_def, "Duration constraint missing lower bound"
            assert '7' in constraint_def, "Duration constraint missing upper bound"
        finally:
            cursor.close()
            return_db_connection(conn)

    def test_adventure_indexes_exist(self):
        """Verify expected indexes exist."""
        conn = get_db_connection()
        if not conn:
            pytest.skip("No database connection")
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT indexname
                FROM pg_indexes
                WHERE tablename = 'adventures';
            """)
            indexes = {row[0] for row in cursor.fetchall()}

            expected_indexes = {
                'idx_adventures_user_id',
                'idx_adventures_status',
                'idx_adventures_user_status',
                'idx_adventures_deadline'
            }
            assert expected_indexes.issubset(indexes), f"Missing indexes: {expected_indexes - indexes}"
        finally:
            cursor.close()
            return_db_connection(conn)

    def test_adventure_foreign_keys(self):
        """Verify foreign key constraints to profiles and monsters."""
        conn = get_db_connection()
        if not conn:
            pytest.skip("No database connection")
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    pg_get_constraintdef(c.oid) as constraint_def
                FROM pg_constraint c
                JOIN pg_namespace n ON n.oid = c.connamespace
                WHERE c.conrelid = 'adventures'::regclass
                AND c.contype = 'f';
            """)
            constraints = [row[0] for row in cursor.fetchall()]

            # Check for foreign key to profiles
            has_profile_fk = any('profiles' in c for c in constraints)
            assert has_profile_fk, "Missing foreign key to profiles table"

            # Check for foreign key to monsters
            has_monster_fk = any('monsters' in c for c in constraints)
            assert has_monster_fk, "Missing foreign key to monsters table"
        finally:
            cursor.close()
            return_db_connection(conn)


@pytest.mark.skipif(not DB_AVAILABLE, reason="Database connection not available")
class TestDailyEntriesModification:
    """Tests for daily_entries table modifications."""

    def test_adventure_id_column_exists(self):
        """Verify adventure_id column was added to daily_entries."""
        conn = get_db_connection()
        if not conn:
            pytest.skip("No database connection")
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns
                    WHERE table_name = 'daily_entries'
                    AND column_name = 'adventure_id'
                );
            """)
            result = cursor.fetchone()
            assert result[0] is True, "adventure_id column does not exist in daily_entries"
        finally:
            cursor.close()
            return_db_connection(conn)

    def test_battle_id_is_nullable(self):
        """Verify battle_id column is now nullable."""
        conn = get_db_connection()
        if not conn:
            pytest.skip("No database connection")
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT is_nullable
                FROM information_schema.columns
                WHERE table_name = 'daily_entries'
                AND column_name = 'battle_id';
            """)
            result = cursor.fetchone()
            assert result is not None, "battle_id column not found"
            assert result[0] == 'YES', "battle_id should be nullable"
        finally:
            cursor.close()
            return_db_connection(conn)

    def test_exclusive_game_mode_constraint(self):
        """Verify constraint enforces exactly one of battle_id or adventure_id."""
        conn = get_db_connection()
        if not conn:
            pytest.skip("No database connection")
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM pg_constraint
                    WHERE conrelid = 'daily_entries'::regclass
                    AND conname = 'daily_entry_game_mode_check'
                );
            """)
            result = cursor.fetchone()
            assert result[0] is True, "daily_entry_game_mode_check constraint does not exist"
        finally:
            cursor.close()
            return_db_connection(conn)

    def test_adventure_index_exists(self):
        """Verify index on adventure_id exists."""
        conn = get_db_connection()
        if not conn:
            pytest.skip("No database connection")
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM pg_indexes
                    WHERE tablename = 'daily_entries'
                    AND indexname = 'idx_daily_entries_adventure_id'
                );
            """)
            result = cursor.fetchone()
            assert result[0] is True, "idx_daily_entries_adventure_id index does not exist"
        finally:
            cursor.close()
            return_db_connection(conn)


@pytest.mark.skipif(not DB_AVAILABLE, reason="Database connection not available")
class TestProfilesModification:
    """Tests for profiles table modifications."""

    def test_adventure_columns_exist(self):
        """Verify all adventure-related columns were added."""
        conn = get_db_connection()
        if not conn:
            pytest.skip("No database connection")
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'profiles'
                AND column_name IN (
                    'current_adventure', 'adventure_count',
                    'monster_defeats', 'monster_escapes', 'monster_rating',
                    'highest_tier_reached'
                );
            """)
            columns = {row[0] for row in cursor.fetchall()}

            expected_columns = {
                'current_adventure', 'adventure_count',
                'monster_defeats', 'monster_escapes', 'monster_rating',
                'highest_tier_reached'
            }
            assert expected_columns == columns, f"Column mismatch. Expected: {expected_columns}, Got: {columns}"
        finally:
            cursor.close()
            return_db_connection(conn)

    def test_monster_rating_non_negative(self):
        """Verify monster_rating has non-negative constraint."""
        conn = get_db_connection()
        if not conn:
            pytest.skip("No database connection")
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM pg_constraint
                    WHERE conrelid = 'profiles'::regclass
                    AND conname = 'monster_rating_non_negative'
                );
            """)
            result = cursor.fetchone()
            assert result[0] is True, "monster_rating_non_negative constraint does not exist"
        finally:
            cursor.close()
            return_db_connection(conn)

    def test_highest_tier_valid_constraint(self):
        """Verify highest_tier_reached has valid tier constraint."""
        conn = get_db_connection()
        if not conn:
            pytest.skip("No database connection")
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM pg_constraint
                    WHERE conrelid = 'profiles'::regclass
                    AND conname = 'highest_tier_valid'
                );
            """)
            result = cursor.fetchone()
            assert result[0] is True, "highest_tier_valid constraint does not exist"
        finally:
            cursor.close()
            return_db_connection(conn)


@pytest.mark.skipif(not DB_AVAILABLE, reason="Database connection not available")
class TestRLSPolicies:
    """Tests for Row Level Security policies."""

    def test_monsters_rls_enabled(self):
        """Verify monsters table has RLS enabled."""
        conn = get_db_connection()
        if not conn:
            pytest.skip("No database connection")
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT relrowsecurity
                FROM pg_class
                WHERE relname = 'monsters';
            """)
            result = cursor.fetchone()
            assert result is not None, "Monsters table not found"
            assert result[0] is True, "RLS not enabled on monsters table"
        finally:
            cursor.close()
            return_db_connection(conn)

    def test_adventures_rls_enabled(self):
        """Verify adventures table has RLS enabled."""
        conn = get_db_connection()
        if not conn:
            pytest.skip("No database connection")
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT relrowsecurity
                FROM pg_class
                WHERE relname = 'adventures';
            """)
            result = cursor.fetchone()
            assert result is not None, "Adventures table not found"
            assert result[0] is True, "RLS not enabled on adventures table"
        finally:
            cursor.close()
            return_db_connection(conn)

    def test_adventures_policies_exist(self):
        """Verify adventures table has expected RLS policies."""
        conn = get_db_connection()
        if not conn:
            pytest.skip("No database connection")
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT policyname
                FROM pg_policies
                WHERE tablename = 'adventures';
            """)
            policies = {row[0] for row in cursor.fetchall()}

            expected_policies = {
                'Users can view their own adventures',
                'Users can insert their own adventures',
                'Users can update their own adventures'
            }
            assert expected_policies.issubset(policies), f"Missing policies: {expected_policies - policies}"
        finally:
            cursor.close()
            return_db_connection(conn)

    def test_monsters_public_read_policy(self):
        """Verify monsters table has public read policy."""
        conn = get_db_connection()
        if not conn:
            pytest.skip("No database connection")
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM pg_policies
                    WHERE tablename = 'monsters'
                    AND policyname = 'Monsters are viewable by everyone'
                );
            """)
            result = cursor.fetchone()
            assert result[0] is True, "Monsters public read policy does not exist"
        finally:
            cursor.close()
            return_db_connection(conn)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
