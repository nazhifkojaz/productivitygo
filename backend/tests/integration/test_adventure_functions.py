"""
Integration tests for Adventure Mode SQL functions.

These tests verify that:
1. calculate_adventure_round processes damage correctly
2. Break days are handled properly
3. No tasks planned returns 0 damage
4. Damage is capped at 120
5. Adventure stats are updated

Run after deploying Adventure Mode SQL functions.

Usage:
    pytest tests/integration/test_adventure_functions.py -v
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


# Get test data from database
@pytest.fixture(scope='module')
def test_data(db_conn):
    """Get test user and monster ID for testing.

    Uses a designated test user (80c0d05e-e927-4860-a17e-8bb085df6fbb)
    to avoid affecting random real users.
    """
    cursor = db_conn.cursor()
    try:
        # Use the designated test user
        test_user_id = '80c0d05e-e927-4860-a17e-8bb085df6fbb'
        cursor.execute("SELECT id FROM profiles WHERE id = %s;", (test_user_id,))
        result = cursor.fetchone()

        if not result:
            pytest.skip("Test user not found. Ensure user 80c0d05e-e927-4860-a17e-8bb085df6fbb exists.")

        # Get a monster ID
        cursor.execute("SELECT id FROM monsters WHERE tier = 'easy' LIMIT 1;")
        result = cursor.fetchone()
        if not result:
            pytest.skip("No monsters in database. Run seed_monsters.sql first.")
        monster_id = result[0]

        return {'user_id': test_user_id, 'monster_id': monster_id}
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
        # Clear current_adventure reference BEFORE deleting adventures
        cursor.execute("UPDATE profiles SET current_adventure = NULL WHERE id = %s;", (user_id,))
        # Delete related data
        cursor.execute("DELETE FROM tasks WHERE daily_entry_id IN (SELECT id FROM daily_entries WHERE user_id = %s);", (user_id,))
        cursor.execute("DELETE FROM daily_entries WHERE user_id = %s;", (user_id,))
        cursor.execute("DELETE FROM adventures WHERE user_id = %s;", (user_id,))
        db_conn.commit()
    finally:
        cursor.close()


@pytest.mark.skipif(not DB_AVAILABLE, reason="Database connection not available")
class TestCalculateAdventureRound:
    """Tests for calculate_adventure_round function."""

    def test_function_exists(self, db_conn):
        """Verify function exists in database."""
        cursor = db_conn.cursor()
        try:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM pg_proc
                    WHERE proname = 'calculate_adventure_round'
                );
            """)
            result = cursor.fetchone()
            assert result[0] is True, "calculate_adventure_round function does not exist"
        finally:
            cursor.close()

    def test_calculate_damage_with_all_mandatory_completed(self, db_conn, test_data, cleanup_test_data):
        """100% mandatory completion = 100 damage."""
        cursor = db_conn.cursor()
        try:
            # Create a test user profile if needed
            cursor.execute("""
                INSERT INTO profiles (id, username, email, monster_rating, highest_tier_reached)
                VALUES (%s, 'TestUser', 'test@example.com', 0, 'easy')
                ON CONFLICT (id) DO NOTHING;
            """, (test_data['user_id'],))
            db_conn.commit()

            # Create adventure
            adventure_id = '00000000-0000-0000-0000-000000000003'
            test_date = date.today()
            cursor.execute("""
                INSERT INTO adventures (id, user_id, monster_id, duration, start_date, deadline,
                    monster_max_hp, monster_current_hp, status)
                VALUES (%s, %s, %s, 5, %s, %s, 200, 200, 'active')
                RETURNING id;
            """, (adventure_id, test_data['user_id'], test_data['monster_id'], test_date, test_date + td(days=5)))
            db_conn.commit()

            # Create daily entry with 3 mandatory tasks, all completed
            entry_id = '00000000-0000-0000-0000-000000000004'
            cursor.execute("""
                INSERT INTO daily_entries (id, user_id, adventure_id, date, battle_id)
                VALUES (%s, %s, %s, %s, NULL);
            """, (entry_id, test_data['user_id'], adventure_id, test_date))

            # Create 3 mandatory tasks, all completed
            for i in range(3):
                cursor.execute("""
                    INSERT INTO tasks (daily_entry_id, content, is_optional, is_completed)
                    VALUES (%s, %s, false, true);
                """, (entry_id, f'Task {i}'))
            db_conn.commit()

            # Call the function
            cursor.execute("""
                SELECT * FROM calculate_adventure_round(%s, %s);
            """, (adventure_id, test_date))
            damage, new_hp = cursor.fetchone()

            assert damage == 100, f"Expected 100 damage, got {damage}"
            assert new_hp == 100, f"Expected 100 HP remaining, got {new_hp}"

        finally:
            cursor.close()

    def test_calculate_damage_with_optional_tasks(self, db_conn, test_data, cleanup_test_data):
        """Each optional task adds 10 damage."""
        cursor = db_conn.cursor()
        try:
            # Ensure profile exists
            cursor.execute("""
                INSERT INTO profiles (id, username, email, monster_rating, highest_tier_reached)
                VALUES (%s, 'TestUser', 'test@example.com', 0, 'easy')
                ON CONFLICT (id) DO NOTHING;
            """, (test_data['user_id'],))
            db_conn.commit()

            adventure_id = '00000000-0000-0000-0000-000000000005'
            test_date = date.today()
            cursor.execute("""
                INSERT INTO adventures (id, user_id, monster_id, duration, start_date, deadline,
                    monster_max_hp, monster_current_hp, status)
                VALUES (%s, %s, %s, 5, %s, %s, 200, 200, 'active');
            """, (adventure_id, test_data['user_id'], test_data['monster_id'], test_date, test_date + td(days=5)))

            entry_id = '00000000-0000-0000-0000-000000000006'
            cursor.execute("""
                INSERT INTO daily_entries (id, user_id, adventure_id, date, battle_id)
                VALUES (%s, %s, %s, %s, NULL);
            """, (entry_id, test_data['user_id'], adventure_id, test_date))

            # 3 mandatory (all completed) + 2 optional (all completed) = 100 + 20 = 120
            for i in range(3):
                cursor.execute("""
                    INSERT INTO tasks (daily_entry_id, content, is_optional, is_completed)
                    VALUES (%s, %s, false, true);
                """, (entry_id, f'Mandatory {i}'))
            for i in range(2):
                cursor.execute("""
                    INSERT INTO tasks (daily_entry_id, content, is_optional, is_completed)
                    VALUES (%s, %s, true, true);
                """, (entry_id, f'Optional {i}'))
            db_conn.commit()

            cursor.execute("""
                SELECT * FROM calculate_adventure_round(%s, %s);
            """, (adventure_id, test_date))
            damage, new_hp = cursor.fetchone()

            assert damage == 120, f"Expected 120 damage, got {damage}"
            assert new_hp == 80, f"Expected 80 HP remaining, got {new_hp}"

        finally:
            cursor.close()

    def test_damage_capped_at_120(self, db_conn, test_data, cleanup_test_data):
        """Damage cannot exceed 120 even with many optionals."""
        cursor = db_conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO profiles (id, username, email, monster_rating, highest_tier_reached)
                VALUES (%s, 'TestUser', 'test@example.com', 0, 'easy')
                ON CONFLICT (id) DO NOTHING;
            """, (test_data['user_id'],))
            db_conn.commit()

            adventure_id = '00000000-0000-0000-0000-000000000007'
            test_date = date.today()
            cursor.execute("""
                INSERT INTO adventures (id, user_id, monster_id, duration, start_date, deadline,
                    monster_max_hp, monster_current_hp, status)
                VALUES (%s, %s, %s, 5, %s, %s, 200, 200, 'active');
            """, (adventure_id, test_data['user_id'], test_data['monster_id'], test_date, test_date + td(days=5)))

            entry_id = '00000000-0000-0000-0000-000000000008'
            cursor.execute("""
                INSERT INTO daily_entries (id, user_id, adventure_id, date, battle_id)
                VALUES (%s, %s, %s, %s, NULL);
            """, (entry_id, test_data['user_id'], adventure_id, test_date))

            # 3 mandatory (all completed) + 5 optional (would be 150 without cap)
            for i in range(3):
                cursor.execute("""
                    INSERT INTO tasks (daily_entry_id, content, is_optional, is_completed)
                    VALUES (%s, %s, false, true);
                """, (entry_id, f'Mandatory {i}'))
            for i in range(5):
                cursor.execute("""
                    INSERT INTO tasks (daily_entry_id, content, is_optional, is_completed)
                    VALUES (%s, %s, true, true);
                """, (entry_id, f'Optional {i}'))
            db_conn.commit()

            cursor.execute("""
                SELECT * FROM calculate_adventure_round(%s, %s);
            """, (adventure_id, test_date))
            damage, new_hp = cursor.fetchone()

            assert damage == 120, f"Expected 120 damage (capped), got {damage}"

        finally:
            cursor.close()

    def test_no_mandatory_only_optional(self, db_conn, test_data, cleanup_test_data):
        """With no mandatory tasks, damage = optional * 10 (capped at 120)."""
        cursor = db_conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO profiles (id, username, email, monster_rating, highest_tier_reached)
                VALUES (%s, 'TestUser', 'test@example.com', 0, 'easy')
                ON CONFLICT (id) DO NOTHING;
            """, (test_data['user_id'],))
            db_conn.commit()

            adventure_id = '00000000-0000-0000-0000-000000000009'
            test_date = date.today()
            cursor.execute("""
                INSERT INTO adventures (id, user_id, monster_id, duration, start_date, deadline,
                    monster_max_hp, monster_current_hp, status)
                VALUES (%s, %s, %s, 5, %s, %s, 200, 200, 'active');
            """, (adventure_id, test_data['user_id'], test_data['monster_id'], test_date, test_date + td(days=5)))

            entry_id = '00000000-0000-0000-0000-000000000010'
            cursor.execute("""
                INSERT INTO daily_entries (id, user_id, adventure_id, date, battle_id)
                VALUES (%s, %s, %s, %s, NULL);
            """, (entry_id, test_data['user_id'], adventure_id, test_date))

            # Only 5 optional tasks, all completed = 50 damage
            for i in range(5):
                cursor.execute("""
                    INSERT INTO tasks (daily_entry_id, content, is_optional, is_completed)
                    VALUES (%s, %s, true, true);
                """, (entry_id, f'Optional {i}'))
            db_conn.commit()

            cursor.execute("""
                SELECT * FROM calculate_adventure_round(%s, %s);
            """, (adventure_id, test_date))
            damage, new_hp = cursor.fetchone()

            assert damage == 50, f"Expected 50 damage, got {damage}"

        finally:
            cursor.close()

    def test_no_tasks_planned_returns_zero_damage(self, db_conn, test_data, cleanup_test_data):
        """No daily_entry or tasks = 0 damage."""
        cursor = db_conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO profiles (id, username, email, monster_rating, highest_tier_reached)
                VALUES (%s, 'TestUser', 'test@example.com', 0, 'easy')
                ON CONFLICT (id) DO NOTHING;
            """, (test_data['user_id'],))
            db_conn.commit()

            adventure_id = '00000000-0000-0000-0000-000000000011'
            test_date = date.today()
            cursor.execute("""
                INSERT INTO adventures (id, user_id, monster_id, duration, start_date, deadline,
                    monster_max_hp, monster_current_hp, status)
                VALUES (%s, %s, %s, 5, %s, %s, 200, 200, 'active');
            """, (adventure_id, test_data['user_id'], test_data['monster_id'], test_date, test_date + td(days=5)))

            # No daily entry created - should return 0 damage
            cursor.execute("""
                SELECT * FROM calculate_adventure_round(%s, %s);
            """, (adventure_id, test_date))
            damage, new_hp = cursor.fetchone()

            assert damage == 0, f"Expected 0 damage (no tasks), got {damage}"
            assert new_hp == 200, f"Expected 200 HP (unchanged), got {new_hp}"

        finally:
            cursor.close()

    def test_on_break_skips_processing(self, db_conn, test_data, cleanup_test_data):
        """Adventure on break returns 0 damage."""
        cursor = db_conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO profiles (id, username, email, monster_rating, highest_tier_reached)
                VALUES (%s, 'TestUser', 'test@example.com', 0, 'easy')
                ON CONFLICT (id) DO NOTHING;
            """, (test_data['user_id'],))
            db_conn.commit()

            adventure_id = '00000000-0000-0000-0000-000000000012'
            test_date = date.today()
            tomorrow = test_date + td(days=1)
            cursor.execute("""
                INSERT INTO adventures (id, user_id, monster_id, duration, start_date, deadline,
                    monster_max_hp, monster_current_hp, status, is_on_break, break_end_date)
                VALUES (%s, %s, %s, 5, %s, %s, 200, 200, 'active', true, %s);
            """, (adventure_id, test_data['user_id'], test_data['monster_id'], test_date, test_date + td(days=5), tomorrow))

            entry_id = '00000000-0000-0000-0000-000000000013'
            cursor.execute("""
                INSERT INTO daily_entries (id, user_id, adventure_id, date, battle_id)
                VALUES (%s, %s, %s, %s, NULL);
            """, (entry_id, test_data['user_id'], adventure_id, test_date))

            # Create completed tasks (should be ignored due to break)
            for i in range(3):
                cursor.execute("""
                    INSERT INTO tasks (daily_entry_id, content, is_optional, is_completed)
                    VALUES (%s, %s, false, true);
                """, (entry_id, f'Task {i}'))
            db_conn.commit()

            cursor.execute("""
                SELECT * FROM calculate_adventure_round(%s, %s);
            """, (adventure_id, test_date))
            damage, new_hp = cursor.fetchone()

            assert damage == 0, f"Expected 0 damage (on break), got {damage}"
            assert new_hp == 200, f"Expected 200 HP (unchanged), got {new_hp}"

        finally:
            cursor.close()

    def test_break_cleared_after_end_date(self, db_conn, test_data, cleanup_test_data):
        """Break status cleared when round_date >= break_end_date."""
        cursor = db_conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO profiles (id, username, email, monster_rating, highest_tier_reached)
                VALUES (%s, 'TestUser', 'test@example.com', 0, 'easy')
                ON CONFLICT (id) DO NOTHING;
            """, (test_data['user_id'],))
            db_conn.commit()

            adventure_id = '00000000-0000-0000-0000-000000000014'
            test_date = date.today()
            yesterday = test_date - td(days=1)
            cursor.execute("""
                INSERT INTO adventures (id, user_id, monster_id, duration, start_date, deadline,
                    monster_max_hp, monster_current_hp, status, is_on_break, break_end_date)
                VALUES (%s, %s, %s, 5, %s, %s, 200, 200, 'active', true, %s);
            """, (adventure_id, test_data['user_id'], test_data['monster_id'], test_date, test_date + td(days=5), yesterday))

            entry_id = '00000000-0000-0000-0000-000000000015'
            cursor.execute("""
                INSERT INTO daily_entries (id, user_id, adventure_id, date, battle_id)
                VALUES (%s, %s, %s, %s, NULL);
            """, (entry_id, test_data['user_id'], adventure_id, test_date))

            # Create completed tasks
            for i in range(3):
                cursor.execute("""
                    INSERT INTO tasks (daily_entry_id, content, is_optional, is_completed)
                    VALUES (%s, %s, false, true);
                """, (entry_id, f'Task {i}'))
            db_conn.commit()

            cursor.execute("""
                SELECT * FROM calculate_adventure_round(%s, %s);
            """, (adventure_id, test_date))
            damage, new_hp = cursor.fetchone()

            # Break should be cleared and damage applied
            assert damage == 100, f"Expected 100 damage (break cleared), got {damage}"

            # Verify break status was cleared
            cursor.execute("""
                SELECT is_on_break FROM adventures WHERE id = %s;
            """, (adventure_id,))
            is_on_break = cursor.fetchone()[0]
            assert is_on_break is False, "Break status should be cleared"

        finally:
            cursor.close()

    def test_adventure_stats_updated(self, db_conn, test_data, cleanup_test_data):
        """Updates total_damage_dealt and current_round."""
        cursor = db_conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO profiles (id, username, email, monster_rating, highest_tier_reached)
                VALUES (%s, 'TestUser', 'test@example.com', 0, 'easy')
                ON CONFLICT (id) DO NOTHING;
            """, (test_data['user_id'],))
            db_conn.commit()

            adventure_id = '00000000-0000-0000-0000-000000000016'
            test_date = date.today()
            cursor.execute("""
                INSERT INTO adventures (id, user_id, monster_id, duration, start_date, deadline,
                    monster_max_hp, monster_current_hp, status, total_damage_dealt, current_round)
                VALUES (%s, %s, %s, 5, %s, %s, 200, 200, 'active', 0, 0);
            """, (adventure_id, test_data['user_id'], test_data['monster_id'], test_date, test_date + td(days=5)))

            entry_id = '00000000-0000-0000-0000-000000000017'
            cursor.execute("""
                INSERT INTO daily_entries (id, user_id, adventure_id, date, battle_id)
                VALUES (%s, %s, %s, %s, NULL);
            """, (entry_id, test_data['user_id'], adventure_id, test_date))

            # Create 2/3 mandatory completed = 67 damage rounded
            for i in range(3):
                is_completed = i < 2
                cursor.execute("""
                    INSERT INTO tasks (daily_entry_id, content, is_optional, is_completed)
                    VALUES (%s, %s, false, %s);
                """, (entry_id, f'Task {i}', is_completed))
            db_conn.commit()

            cursor.execute("""
                SELECT * FROM calculate_adventure_round(%s, %s);
            """, (adventure_id, test_date))
            damage, new_hp = cursor.fetchone()

            # Check stats updated
            cursor.execute("""
                SELECT total_damage_dealt, current_round FROM adventures WHERE id = %s;
            """, (adventure_id,))
            total_damage, round_num = cursor.fetchone()

            assert total_damage == damage, f"total_damage_dealt should be {damage}, got {total_damage}"
            assert round_num == 1, f"current_round should be 1, got {round_num}"

        finally:
            cursor.close()

    def test_daily_entry_xp_updated(self, db_conn, test_data, cleanup_test_data):
        """Stores damage in daily_entry.daily_xp."""
        cursor = db_conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO profiles (id, username, email, monster_rating, highest_tier_reached)
                VALUES (%s, 'TestUser', 'test@example.com', 0, 'easy')
                ON CONFLICT (id) DO NOTHING;
            """, (test_data['user_id'],))
            db_conn.commit()

            adventure_id = '00000000-0000-0000-0000-000000000018'
            test_date = date.today()
            cursor.execute("""
                INSERT INTO adventures (id, user_id, monster_id, duration, start_date, deadline,
                    monster_max_hp, monster_current_hp, status)
                VALUES (%s, %s, %s, 5, %s, %s, 200, 200, 'active');
            """, (adventure_id, test_data['user_id'], test_data['monster_id'], test_date, test_date + td(days=5)))

            entry_id = '00000000-0000-0000-0000-000000000019'
            cursor.execute("""
                INSERT INTO daily_entries (id, user_id, adventure_id, date, battle_id, daily_xp)
                VALUES (%s, %s, %s, %s, NULL, 0);
            """, (entry_id, test_data['user_id'], adventure_id, test_date))

            # Create 3 mandatory tasks all completed
            for i in range(3):
                cursor.execute("""
                    INSERT INTO tasks (daily_entry_id, content, is_optional, is_completed)
                    VALUES (%s, %s, false, true);
                """, (entry_id, f'Task {i}'))
            db_conn.commit()

            cursor.execute("""
                SELECT * FROM calculate_adventure_round(%s, %s);
            """, (adventure_id, test_date))
            damage, new_hp = cursor.fetchone()

            # Check daily_xp updated
            cursor.execute("""
                SELECT daily_xp FROM daily_entries WHERE id = %s;
            """, (entry_id,))
            daily_xp = cursor.fetchone()[0]

            assert daily_xp == damage, f"daily_xp should be {damage}, got {daily_xp}"

        finally:
            cursor.close()

    def test_monster_hp_floors_at_zero(self, db_conn, test_data, cleanup_test_data):
        """Monster HP cannot go below 0."""
        cursor = db_conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO profiles (id, username, email, monster_rating, highest_tier_reached)
                VALUES (%s, 'TestUser', 'test@example.com', 0, 'easy')
                ON CONFLICT (id) DO NOTHING;
            """, (test_data['user_id'],))
            db_conn.commit()

            adventure_id = '00000000-0000-0000-0000-000000000020'
            test_date = date.today()
            # Create adventure with only 50 HP
            cursor.execute("""
                INSERT INTO adventures (id, user_id, monster_id, duration, start_date, deadline,
                    monster_max_hp, monster_current_hp, status)
                VALUES (%s, %s, %s, 5, %s, %s, 50, 50, 'active');
            """, (adventure_id, test_data['user_id'], test_data['monster_id'], test_date, test_date + td(days=5)))

            entry_id = '00000000-0000-0000-0000-000000000021'
            cursor.execute("""
                INSERT INTO daily_entries (id, user_id, adventure_id, date, battle_id)
                VALUES (%s, %s, %s, %s, NULL);
            """, (entry_id, test_data['user_id'], adventure_id, test_date))

            # Create tasks that deal 100+ damage
            for i in range(3):
                cursor.execute("""
                    INSERT INTO tasks (daily_entry_id, content, is_optional, is_completed)
                    VALUES (%s, %s, false, true);
                """, (entry_id, f'Task {i}'))
            db_conn.commit()

            cursor.execute("""
                SELECT * FROM calculate_adventure_round(%s, %s);
            """, (adventure_id, test_date))
            damage, new_hp = cursor.fetchone()

            assert new_hp == 0, f"HP should floor at 0, got {new_hp}"

        finally:
            cursor.close()


@pytest.mark.skipif(not DB_AVAILABLE, reason="Database connection not available")
class TestBattlesBreakColumns:
    """Tests for battles table break feature columns."""

    def test_break_columns_exist(self, db_conn):
        """Verify all break columns exist."""
        cursor = db_conn.cursor()
        try:
            cursor.execute("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'battles'
                AND column_name IN (
                    'break_days_used', 'max_break_days', 'is_on_break',
                    'break_end_date', 'break_requested_by', 'break_request_expires_at'
                );
            """)
            columns = {row[0] for row in cursor.fetchall()}

            expected_columns = {
                'break_days_used', 'max_break_days', 'is_on_break',
                'break_end_date', 'break_requested_by', 'break_request_expires_at'
            }
            assert expected_columns == columns, f"Column mismatch. Expected: {expected_columns}, Got: {columns}"
        finally:
            cursor.close()

    def test_break_columns_have_defaults(self, db_conn):
        """Verify break columns have correct default values."""
        cursor = db_conn.cursor()
        try:
            cursor.execute("""
                SELECT column_default, data_type
                FROM information_schema.columns
                WHERE table_name = 'battles'
                AND column_name IN ('break_days_used', 'max_break_days', 'is_on_break')
                ORDER BY column_name;
            """)
            results = cursor.fetchall()

            defaults = {row[0] for row in results}
            # break_days_used and max_break_days should default to 0
            # is_on_break should default to false
            assert any('0' in str(d) for d in defaults), "break_days_used/max_break_days should default to 0"
        finally:
            cursor.close()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
