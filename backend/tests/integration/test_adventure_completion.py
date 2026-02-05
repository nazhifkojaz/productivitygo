"""
Integration tests for Adventure Mode completion functions.

These tests verify that:
1. complete_adventure works for victory (HP <= 0)
2. complete_adventure works for escape (HP > 0 at deadline)
3. complete_adventure is idempotent
4. abandon_adventure works with proper ownership check
5. abandon_adventure rejects non-owners
6. abandon_adventure rejects already completed adventures
7. XP calculated correctly with tier multipliers
8. User stats updated correctly
9. get_unlocked_tiers returns correct tiers
10. highest_tier_reached updates correctly

Run after deploying Adventure Mode completion functions.

Usage:
    pytest tests/integration/test_adventure_completion.py -v
"""
import pytest
import sys
import os
from datetime import date, timedelta as td

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    from database import get_db_connection, return_db_connection
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False


# Get real test data from database
@pytest.fixture(scope='module')
def test_data(db_conn):
    """Get real user and monster IDs from database for testing."""
    cursor = db_conn.cursor()
    try:
        # Get a real user ID from profiles
        cursor.execute("SELECT id FROM profiles LIMIT 1;")
        result = cursor.fetchone()
        if not result:
            pytest.skip("No users in profiles table. Create a test user first.")
        user_id = result[0]

        # Get monsters of different tiers
        cursor.execute("SELECT id, tier FROM monsters WHERE tier = 'easy' LIMIT 1;")
        easy_result = cursor.fetchone()
        if not easy_result:
            pytest.skip("No easy monsters in database.")
        easy_monster_id = easy_result[0]

        cursor.execute("SELECT id, tier FROM monsters WHERE tier = 'medium' LIMIT 1;")
        medium_result = cursor.fetchone()
        if not medium_result:
            pytest.skip("No medium monsters in database.")
        medium_monster_id = medium_result[0]

        cursor.execute("SELECT id, tier FROM monsters WHERE tier = 'boss' LIMIT 1;")
        boss_result = cursor.fetchone()
        boss_monster_id = boss_result[0] if boss_result else easy_monster_id

        return {
            'user_id': user_id,
            'easy_monster_id': easy_monster_id,
            'medium_monster_id': medium_monster_id,
            'boss_monster_id': boss_monster_id
        }
    finally:
        cursor.close()


@pytest.fixture(scope='module')
def db_conn():
    """Shared database connection for all tests."""
    if not DB_AVAILABLE:
        pytest.skip("Database connection not available")

    conn = get_db_connection()
    if not conn:
        pytest.skip("Could not get database connection")
    yield conn
    return_db_connection(conn)


@pytest.fixture
def cleanup_test_data(db_conn, test_data):
    """Cleanup test adventures after each test."""
    user_id = test_data['user_id']
    yield
    cursor = db_conn.cursor()
    try:
        # Rollback any pending transaction first
        db_conn.rollback()
        # Clear current_adventure reference before deleting adventures
        cursor.execute("UPDATE profiles SET current_adventure = NULL WHERE id = %s;", (user_id,))
        cursor.execute("DELETE FROM tasks WHERE daily_entry_id IN (SELECT id FROM daily_entries WHERE user_id = %s);", (user_id,))
        cursor.execute("DELETE FROM daily_entries WHERE user_id = %s;", (user_id,))
        cursor.execute("DELETE FROM adventures WHERE user_id = %s;", (user_id,))
        db_conn.commit()
    finally:
        cursor.close()


@pytest.fixture
def reset_profile_stats(db_conn, test_data):
    """Reset user's adventure stats before tests and restore after."""
    user_id = test_data['user_id']

    cursor = db_conn.cursor()
    try:
        # Get current stats
        cursor.execute("""
            SELECT adventure_count, adventure_win_count, monster_defeats,
                   monster_escapes, monster_rating, highest_tier_reached
            FROM profiles WHERE id = %s;
        """, (user_id,))
        original_stats = cursor.fetchone()

        # Reset to 0 for clean testing
        cursor.execute("""
            UPDATE profiles SET
                adventure_count = 0,
                adventure_win_count = 0,
                monster_defeats = 0,
                monster_escapes = 0,
                monster_rating = 0,
                highest_tier_reached = 'easy',
                current_adventure = NULL
            WHERE id = %s;
        """, (user_id,))
        db_conn.commit()

        yield

        # Restore original stats
        cursor.execute("""
            UPDATE profiles SET
                adventure_count = %s,
                adventure_win_count = %s,
                monster_defeats = %s,
                monster_escapes = %s,
                monster_rating = %s,
                highest_tier_reached = %s,
                current_adventure = NULL
            WHERE id = %s;
        """, (*original_stats, user_id))
        db_conn.commit()
    finally:
        cursor.close()


@pytest.mark.skipif(not DB_AVAILABLE, reason="Database connection not available")
class TestGetUnlockedTiers:
    """Tests for get_unlocked_tiers helper function."""

    def test_function_exists(self, db_conn):
        """Verify function exists in database."""
        cursor = db_conn.cursor()
        try:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM pg_proc
                    WHERE proname = 'get_unlocked_tiers'
                );
            """)
            result = cursor.fetchone()
            assert result[0] is True, "get_unlocked_tiers function does not exist"
        finally:
            cursor.close()

    def test_rating_0_returns_easy_only(self, db_conn):
        """Rating 0-1 returns only easy tier."""
        cursor = db_conn.cursor()
        try:
            cursor.execute("SELECT get_unlocked_tiers(0);")
            result = cursor.fetchone()[0]
            assert result == ['easy'], f"Expected ['easy'], got {result}"
        finally:
            cursor.close()

    def test_rating_2_unlocks_medium(self, db_conn):
        """Rating 2-4 unlocks medium tier."""
        cursor = db_conn.cursor()
        try:
            cursor.execute("SELECT get_unlocked_tiers(2);")
            result = cursor.fetchone()[0]
            assert set(result) == {'easy', 'medium'}, f"Expected easy+medium, got {result}"
        finally:
            cursor.close()

    def test_rating_5_unlocks_hard(self, db_conn):
        """Rating 5-8 unlocks hard tier."""
        cursor = db_conn.cursor()
        try:
            cursor.execute("SELECT get_unlocked_tiers(5);")
            result = cursor.fetchone()[0]
            assert set(result) == {'easy', 'medium', 'hard'}, f"Expected easy+medium+hard, got {result}"
        finally:
            cursor.close()

    def test_rating_9_unlocks_expert(self, db_conn):
        """Rating 9-13 unlocks expert tier."""
        cursor = db_conn.cursor()
        try:
            cursor.execute("SELECT get_unlocked_tiers(9);")
            result = cursor.fetchone()[0]
            assert set(result) == {'easy', 'medium', 'hard', 'expert'}, f"Expected up to expert, got {result}"
        finally:
            cursor.close()

    def test_rating_14_unlocks_boss(self, db_conn):
        """Rating 14+ unlocks boss tier (all tiers)."""
        cursor = db_conn.cursor()
        try:
            cursor.execute("SELECT get_unlocked_tiers(14);")
            result = cursor.fetchone()[0]
            assert set(result) == {'easy', 'medium', 'hard', 'expert', 'boss'}, f"Expected all tiers, got {result}"
        finally:
            cursor.close()


@pytest.mark.skipif(not DB_AVAILABLE, reason="Database connection not available")
class TestCompleteAdventure:
    """Tests for complete_adventure function."""

    def test_function_exists(self, db_conn):
        """Verify function exists in database."""
        cursor = db_conn.cursor()
        try:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM pg_proc
                    WHERE proname = 'complete_adventure'
                );
            """)
            result = cursor.fetchone()
            assert result[0] is True, "complete_adventure function does not exist"
        finally:
            cursor.close()

    def test_victory_when_hp_zero(self, db_conn, test_data, cleanup_test_data, reset_profile_stats):
        """Adventure completes with victory when monster HP reaches 0."""
        cursor = db_conn.cursor()
        try:
            test_date = date.today()
            adventure_id = '00000000-0000-0000-0000-000000000030'
            user_id = test_data['user_id']
            monster_id = test_data['easy_monster_id']

            # Create adventure with monster at 0 HP (defeated)
            cursor.execute("""
                INSERT INTO adventures (id, user_id, monster_id, duration, start_date, deadline,
                    monster_max_hp, monster_current_hp, status, total_damage_dealt)
                VALUES (%s, %s, %s, 5, %s, %s, 200, 0, 'active', 200);
            """, (adventure_id, user_id, monster_id, test_date, test_date + td(days=5)))
            db_conn.commit()

            # Complete adventure
            cursor.execute("SELECT * FROM complete_adventure(%s);", (adventure_id,))
            status, is_victory, xp_earned, already_completed = cursor.fetchone()

            assert status == 'completed', f"Expected 'completed', got '{status}'"
            assert is_victory is True, f"Expected victory=True"
            assert xp_earned == 200, f"Expected 200 XP (200*1.0), got {xp_earned}"
            assert already_completed is False, "Should not be already_completed"

        finally:
            cursor.close()

    def test_escape_when_hp_remaining(self, db_conn, test_data, cleanup_test_data, reset_profile_stats):
        """Adventure escapes when deadline passes with HP remaining."""
        cursor = db_conn.cursor()
        try:
            test_date = date.today()
            adventure_id = '00000000-0000-0000-0000-000000000031'
            user_id = test_data['user_id']
            monster_id = test_data['easy_monster_id']

            # Create adventure with monster at 100 HP (not defeated)
            cursor.execute("""
                INSERT INTO adventures (id, user_id, monster_id, duration, start_date, deadline,
                    monster_max_hp, monster_current_hp, status, total_damage_dealt)
                VALUES (%s, %s, %s, 5, %s, %s, 200, 100, 'active', 100);
            """, (adventure_id, user_id, monster_id, test_date, test_date + td(days=5)))
            db_conn.commit()

            # Complete adventure
            cursor.execute("SELECT * FROM complete_adventure(%s);", (adventure_id,))
            status, is_victory, xp_earned, already_completed = cursor.fetchone()

            assert status == 'escaped', f"Expected 'escaped', got '{status}'"
            assert is_victory is False, f"Expected victory=False"
            assert xp_earned == 50, f"Expected 50 XP (100*1.0*0.5), got {xp_earned}"
            assert already_completed is False, "Should not be already_completed"

        finally:
            cursor.close()

    def test_is_idempotent(self, db_conn, test_data, cleanup_test_data, reset_profile_stats):
        """Can call complete_adventure multiple times safely."""
        cursor = db_conn.cursor()
        try:
            test_date = date.today()
            adventure_id = '00000000-0000-0000-0000-000000000032'
            user_id = test_data['user_id']
            monster_id = test_data['easy_monster_id']

            # Create adventure
            cursor.execute("""
                INSERT INTO adventures (id, user_id, monster_id, duration, start_date, deadline,
                    monster_max_hp, monster_current_hp, status, total_damage_dealt)
                VALUES (%s, %s, %s, 5, %s, %s, 200, 0, 'active', 200);
            """, (adventure_id, user_id, monster_id, test_date, test_date + td(days=5)))
            db_conn.commit()

            # First completion
            cursor.execute("SELECT * FROM complete_adventure(%s);", (adventure_id,))
            status1, is_victory1, xp1, already1 = cursor.fetchone()

            # Second completion (should return already_completed=True)
            cursor.execute("SELECT * FROM complete_adventure(%s);", (adventure_id,))
            status2, is_victory2, xp2, already2 = cursor.fetchone()

            assert already1 is False, "First call should not be already_completed"
            assert already2 is True, "Second call should be already_completed"
            assert xp1 == xp2, "XP should be same on both calls"

        finally:
            cursor.close()

    def test_updates_profile_stats_on_victory(self, db_conn, test_data, cleanup_test_data, reset_profile_stats):
        """Victory updates user profile stats correctly."""
        cursor = db_conn.cursor()
        try:
            test_date = date.today()
            adventure_id = '00000000-0000-0000-0000-000000000033'
            user_id = test_data['user_id']
            monster_id = test_data['easy_monster_id']

            # Create adventure
            cursor.execute("""
                INSERT INTO adventures (id, user_id, monster_id, duration, start_date, deadline,
                    monster_max_hp, monster_current_hp, status, total_damage_dealt)
                VALUES (%s, %s, %s, 5, %s, %s, 200, 0, 'active', 200);
            """, (adventure_id, user_id, monster_id, test_date, test_date + td(days=5)))
            db_conn.commit()

            # Complete adventure
            cursor.execute("SELECT * FROM complete_adventure(%s);", (adventure_id,))
            cursor.fetchone()

            # Check profile stats
            cursor.execute("""
                SELECT adventure_count, adventure_win_count, monster_defeats,
                       monster_escapes, monster_rating
                FROM profiles WHERE id = %s;
            """, (user_id,))
            stats = cursor.fetchone()

            assert stats[0] == 1, f"adventure_count should be 1, got {stats[0]}"
            assert stats[1] == 1, f"adventure_win_count should be 1, got {stats[1]}"
            assert stats[2] == 1, f"monster_defeats should be 1, got {stats[2]}"
            assert stats[3] == 0, f"monster_escapes should be 0, got {stats[3]}"
            assert stats[4] == 1, f"monster_rating should be 1, got {stats[4]}"

        finally:
            cursor.close()

    def test_updates_profile_stats_on_escape(self, db_conn, test_data, cleanup_test_data, reset_profile_stats):
        """Escape updates user profile stats correctly."""
        cursor = db_conn.cursor()
        try:
            test_date = date.today()
            adventure_id = '00000000-0000-0000-0000-000000000034'
            user_id = test_data['user_id']
            monster_id = test_data['easy_monster_id']

            # Create adventure (not defeated)
            cursor.execute("""
                INSERT INTO adventures (id, user_id, monster_id, duration, start_date, deadline,
                    monster_max_hp, monster_current_hp, status, total_damage_dealt)
                VALUES (%s, %s, %s, 5, %s, %s, 200, 100, 'active', 100);
            """, (adventure_id, user_id, monster_id, test_date, test_date + td(days=5)))
            db_conn.commit()

            # Complete adventure
            cursor.execute("SELECT * FROM complete_adventure(%s);", (adventure_id,))
            cursor.fetchone()

            # Check profile stats
            cursor.execute("""
                SELECT adventure_count, adventure_win_count, monster_defeats,
                       monster_escapes, monster_rating
                FROM profiles WHERE id = %s;
            """, (user_id,))
            stats = cursor.fetchone()

            assert stats[0] == 1, f"adventure_count should be 1"
            assert stats[1] == 0, f"adventure_win_count should be 0"
            assert stats[2] == 0, f"monster_defeats should be 0"
            assert stats[3] == 1, f"monster_escapes should be 1"
            assert stats[4] == 0, f"monster_rating should be 0 (floored)"

        finally:
            cursor.close()

    def test_tier_multiplier_medium(self, db_conn, test_data, cleanup_test_data, reset_profile_stats):
        """Medium tier has 1.2x XP multiplier."""
        cursor = db_conn.cursor()
        try:
            test_date = date.today()
            adventure_id = '00000000-0000-0000-0000-000000000035'
            user_id = test_data['user_id']
            monster_id = test_data['medium_monster_id']

            # Create adventure with 200 damage dealt
            cursor.execute("""
                INSERT INTO adventures (id, user_id, monster_id, duration, start_date, deadline,
                    monster_max_hp, monster_current_hp, status, total_damage_dealt)
                VALUES (%s, %s, %s, 5, %s, %s, 200, 0, 'active', 200);
            """, (adventure_id, user_id, monster_id, test_date, test_date + td(days=5)))
            db_conn.commit()

            # Complete adventure
            cursor.execute("SELECT * FROM complete_adventure(%s);", (adventure_id,))
            status, is_victory, xp_earned, already_completed = cursor.fetchone()

            expected_xp = int(200 * 1.2)  # 240
            assert xp_earned == expected_xp, f"Expected {expected_xp} XP (200*1.2), got {xp_earned}"

        finally:
            cursor.close()

    def test_clears_current_adventure_on_complete(self, db_conn, test_data, cleanup_test_data):
        """Completing adventure clears current_adventure in profile."""
        import uuid
        cursor = db_conn.cursor()
        try:
            test_date = date.today()
            adventure_id = str(uuid.uuid4())  # Unique UUID to avoid conflicts
            user_id = test_data['user_id']
            monster_id = test_data['easy_monster_id']

            # Create adventure
            cursor.execute("""
                INSERT INTO adventures (id, user_id, monster_id, duration, start_date, deadline,
                    monster_max_hp, monster_current_hp, status, total_damage_dealt)
                VALUES (%s, %s, %s, 5, %s, %s, 200, 0, 'active', 200);
            """, (adventure_id, user_id, monster_id, test_date, test_date + td(days=5)))

            # Set current_adventure in profile
            cursor.execute("""
                UPDATE profiles SET current_adventure = %s WHERE id = %s;
            """, (adventure_id, user_id))
            db_conn.commit()

            # Complete adventure
            cursor.execute("SELECT * FROM complete_adventure(%s);", (adventure_id,))
            cursor.fetchone()

            # Check current_adventure is cleared
            cursor.execute("SELECT current_adventure FROM profiles WHERE id = %s;", (user_id,))
            current = cursor.fetchone()[0]

            assert current is None, f"current_adventure should be NULL, got {current}"

        finally:
            cursor.close()

    def test_updates_highest_tier_reached(self, db_conn, test_data, cleanup_test_data):
        """Victory updates highest_tier_reached progressively."""
        cursor = db_conn.cursor()
        try:
            test_date = date.today()
            user_id = test_data['user_id']

            # Start with easy tier as highest
            cursor.execute("""
                UPDATE profiles SET highest_tier_reached = 'easy' WHERE id = %s;
            """, (user_id,))

            # Defeat medium monster
            adventure_id = '00000000-0000-0000-0000-000000000037'
            cursor.execute("""
                INSERT INTO adventures (id, user_id, monster_id, duration, start_date, deadline,
                    monster_max_hp, monster_current_hp, status, total_damage_dealt)
                VALUES (%s, %s, %s, 5, %s, %s, 200, 0, 'active', 200);
            """, (adventure_id, user_id, test_data['medium_monster_id'], test_date, test_date + td(days=5)))
            db_conn.commit()

            cursor.execute("SELECT * FROM complete_adventure(%s);", (adventure_id,))
            cursor.fetchone()

            # Check highest_tier_reached updated
            cursor.execute("SELECT highest_tier_reached FROM profiles WHERE id = %s;", (user_id,))
            highest = cursor.fetchone()[0]

            assert highest == 'medium', f"highest_tier_reached should be 'medium', got '{highest}'"

        finally:
            cursor.close()


@pytest.mark.skipif(not DB_AVAILABLE, reason="Database connection not available")
class TestAbandonAdventure:
    """Tests for abandon_adventure function."""

    def test_function_exists(self, db_conn):
        """Verify function exists in database."""
        cursor = db_conn.cursor()
        try:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM pg_proc
                    WHERE proname = 'abandon_adventure'
                );
            """)
            result = cursor.fetchone()
            assert result[0] is True, "abandon_adventure function does not exist"
        finally:
            cursor.close()

    def test_abandon_grants_half_xp(self, db_conn, test_data, cleanup_test_data, reset_profile_stats):
        """Abandoning rewards 50% XP with tier multiplier."""
        cursor = db_conn.cursor()
        try:
            test_date = date.today()
            adventure_id = '00000000-0000-0000-0000-000000000040'
            user_id = test_data['user_id']
            monster_id = test_data['easy_monster_id']

            # Create adventure with 200 damage dealt
            cursor.execute("""
                INSERT INTO adventures (id, user_id, monster_id, duration, start_date, deadline,
                    monster_max_hp, monster_current_hp, status, total_damage_dealt)
                VALUES (%s, %s, %s, 5, %s, %s, 200, 100, 'active', 100);
            """, (adventure_id, user_id, monster_id, test_date, test_date + td(days=5)))
            db_conn.commit()

            # Abandon adventure
            cursor.execute("SELECT * FROM abandon_adventure(%s, %s);", (adventure_id, user_id))
            status, xp_earned = cursor.fetchone()

            expected_xp = int(100 * 1.0 * 0.5)  # 50
            assert status == 'escaped', f"Expected 'escaped', got '{status}'"
            assert xp_earned == expected_xp, f"Expected {expected_xp} XP, got {xp_earned}"

        finally:
            cursor.close()

    def test_abandon_counts_as_escape(self, db_conn, test_data, cleanup_test_data, reset_profile_stats):
        """Abandoning counts as escape (-1 rating)."""
        cursor = db_conn.cursor()
        try:
            test_date = date.today()
            adventure_id = '00000000-0000-0000-0000-000000000041'
            user_id = test_data['user_id']
            monster_id = test_data['easy_monster_id']

            # Create adventure
            cursor.execute("""
                INSERT INTO adventures (id, user_id, monster_id, duration, start_date, deadline,
                    monster_max_hp, monster_current_hp, status, total_damage_dealt)
                VALUES (%s, %s, %s, 5, %s, %s, 200, 100, 'active', 100);
            """, (adventure_id, user_id, monster_id, test_date, test_date + td(days=5)))
            db_conn.commit()

            # Abandon adventure
            cursor.execute("SELECT * FROM abandon_adventure(%s, %s);", (adventure_id, user_id))
            cursor.fetchone()

            # Check profile stats
            cursor.execute("""
                SELECT monster_escapes, monster_rating FROM profiles WHERE id = %s;
            """, (user_id,))
            escapes, rating = cursor.fetchone()

            assert escapes == 1, f"monster_escapes should be 1, got {escapes}"
            assert rating == 0, f"monster_rating should be 0 (floored from -1), got {rating}"

        finally:
            cursor.close()

    def test_abandon_rejects_non_owner(self, db_conn, test_data, cleanup_test_data):
        """Only adventure owner can abandon."""
        cursor = db_conn.cursor()
        try:
            test_date = date.today()
            adventure_id = '00000000-0000-0000-0000-000000000042'
            user_id = test_data['user_id']
            other_user_id = '00000000-0000-0000-0000-000000000999'
            monster_id = test_data['easy_monster_id']

            # Create adventure
            cursor.execute("""
                INSERT INTO adventures (id, user_id, monster_id, duration, start_date, deadline,
                    monster_max_hp, monster_current_hp, status, total_damage_dealt)
                VALUES (%s, %s, %s, 5, %s, %s, 200, 100, 'active', 100);
            """, (adventure_id, user_id, monster_id, test_date, test_date + td(days=5)))
            db_conn.commit()

            # Try to abandon with wrong user
            with pytest.raises(Exception) as exc_info:
                cursor.execute("SELECT * FROM abandon_adventure(%s, %s);", (adventure_id, other_user_id))
                cursor.fetchone()

            assert 'Not your adventure' in str(exc_info.value)

        finally:
            cursor.close()

    def test_abandon_rejects_completed_adventure(self, db_conn, test_data, cleanup_test_data):
        """Cannot abandon an already completed adventure."""
        cursor = db_conn.cursor()
        try:
            test_date = date.today()
            adventure_id = '00000000-0000-0000-0000-000000000043'
            user_id = test_data['user_id']
            monster_id = test_data['easy_monster_id']

            # Create completed adventure
            cursor.execute("""
                INSERT INTO adventures (id, user_id, monster_id, duration, start_date, deadline,
                    monster_max_hp, monster_current_hp, status, total_damage_dealt, completed_at)
                VALUES (%s, %s, %s, 5, %s, %s, 200, 0, 'completed', 200, NOW());
            """, (adventure_id, user_id, monster_id, test_date, test_date + td(days=5)))
            db_conn.commit()

            # Try to abandon
            with pytest.raises(Exception) as exc_info:
                cursor.execute("SELECT * FROM abandon_adventure(%s, %s);", (adventure_id, user_id))
                cursor.fetchone()

            assert 'not active' in str(exc_info.value).lower()

        finally:
            cursor.close()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
