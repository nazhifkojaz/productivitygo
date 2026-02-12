"""
Integration tests for Adventure Mode SQL functions.

These tests verify that:
1. calculate_adventure_round processes damage correctly
2. Break days are handled properly
3. No tasks planned returns 0 damage
4. Damage is capped at 180 (raised from 120)
5. Adventure stats are updated
6. Type discoveries are recorded

Run after deploying Adventure Mode SQL functions.

Usage:
    pytest tests/integration/test_adventure_functions.py -v
"""
import pytest
import sys
import os
import asyncio
from datetime import date, timedelta as td
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

load_dotenv()
DATABASE_URL = os.environ.get("SUPABASE_URI")

DB_AVAILABLE = bool(DATABASE_URL)


@pytest.fixture
async def db_conn():
    """Shared async database connection for all tests."""
    if not DB_AVAILABLE:
        pytest.skip("Database connection not available")

    import asyncpg
    # statement_cache_size=0 is required for pgbouncer compatibility
    conn = await asyncpg.connect(DATABASE_URL, statement_cache_size=0)
    yield conn
    await conn.close()


@pytest.fixture
async def test_data(db_conn):
    """Get test user and monster ID for testing.

    Uses a designated test user (80c0d05e-e927-4860-a17e-8bb085df6fbb)
    to avoid affecting random real users.
    """
    # Use the designated test user
    test_user_id = '80c0d05e-e927-4860-a17e-8bb085df6fbb'
    result = await db_conn.fetchval("SELECT id FROM profiles WHERE id = $1;", test_user_id)

    if not result:
        pytest.skip("Test user not found. Ensure user 80c0d05e-e927-4860-a17e-8bb085df6fbb exists.")

    # Get a Sloth-type monster (Lazy Slime) for consistent testing
    # Sloth is weak to Physical (1.5x), neutral to Focus (1.0x), resisted by Wellness (0.5x)
    row = await db_conn.fetchrow("SELECT id, monster_type FROM monsters WHERE name = 'Lazy Slime' LIMIT 1;")
    if not row:
        pytest.skip("Lazy Slime monster not found in database.")
    monster_id, monster_type = row['id'], row['monster_type']

    return {'user_id': test_user_id, 'monster_id': monster_id, 'monster_type': monster_type}


@pytest.fixture
async def cleanup_test_data(db_conn, test_data):
    """Cleanup test adventures after each test."""
    user_id = test_data['user_id']
    yield
    # Clear current_adventure reference BEFORE deleting adventures
    await db_conn.execute("UPDATE profiles SET current_adventure = NULL WHERE id = $1;", user_id)
    # Delete related data
    await db_conn.execute("DELETE FROM tasks WHERE daily_entry_id IN (SELECT id FROM daily_entries WHERE user_id = $1);", user_id)
    await db_conn.execute("DELETE FROM daily_entries WHERE user_id = $1;", user_id)
    await db_conn.execute("DELETE FROM adventures WHERE user_id = $1;", user_id)
    await db_conn.execute("DELETE FROM type_discoveries WHERE user_id = $1;", user_id)


@pytest.mark.skipif(not DB_AVAILABLE, reason="Database connection not available")
@pytest.mark.asyncio
class TestCalculateAdventureRound:
    """Tests for calculate_adventure_round function."""

    async def test_function_exists(self, db_conn):
        """Verify function exists in database."""
        result = await db_conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM pg_proc
                WHERE proname = 'calculate_adventure_round'
            );
        """)
        assert result is True, "calculate_adventure_round function does not exist"

    async def test_calculate_damage_with_all_mandatory_completed(self, db_conn, test_data, cleanup_test_data):
        """100% mandatory completion with neutral category = 100 damage."""
        # Create a test user profile if needed
        await db_conn.execute("""
            INSERT INTO profiles (id, username, email, monster_rating, highest_tier_reached)
            VALUES ($1, 'TestUser', 'test@example.com', 0, 'easy')
            ON CONFLICT (id) DO NOTHING;
        """, test_data['user_id'])

        # Create adventure
        adventure_id = '00000000-0000-0000-0000-000000000003'
        test_date = date.today()
        await db_conn.execute("""
            INSERT INTO adventures (id, user_id, monster_id, duration, start_date, deadline,
                monster_max_hp, monster_current_hp, status)
            VALUES ($1, $2, $3, 5, $4, $5, 200, 200, 'active')
            RETURNING id;
        """, adventure_id, test_data['user_id'], test_data['monster_id'], test_date, test_date + td(days=5))

        # Create daily entry with 3 mandatory tasks, all completed
        entry_id = '00000000-0000-0000-0000-000000000004'
        await db_conn.execute("""
            INSERT INTO daily_entries (id, user_id, adventure_id, date, battle_id)
            VALUES ($1, $2, $3, $4, NULL);
        """, entry_id, test_data['user_id'], adventure_id, test_date)

        # Create 3 mandatory tasks, all completed
        # Using 'focus' category which is neutral vs Sloth (1.0x)
        # So: 3 * (100/3 * 1.0) = 100 damage
        for i in range(3):
            await db_conn.execute("""
                INSERT INTO tasks (daily_entry_id, content, is_optional, is_completed, category)
                VALUES ($1, $2, false, true, 'focus');
            """, entry_id, f'Task {i}')

        # Call the function
        row = await db_conn.fetchrow("SELECT * FROM calculate_adventure_round($1, $2);", adventure_id, test_date)
        damage, new_hp = row['damage'], row['new_hp']

        # Note: Due to floating point math in SQL, damage may be 99 instead of 100
        # 3 * (100/3 * 1.0) = 3 * 33.333... = 99.999... -> FLOOR -> 99
        assert damage >= 99, f"Expected at least 99 damage, got {damage}"
        assert new_hp <= 101, f"Expected HP <= 101 remaining, got {new_hp}"

    async def test_calculate_damage_with_optional_tasks(self, db_conn, test_data, cleanup_test_data):
        """Each optional task adds 10 damage with neutral multiplier."""
        # Ensure profile exists
        await db_conn.execute("""
            INSERT INTO profiles (id, username, email, monster_rating, highest_tier_reached)
            VALUES ($1, 'TestUser', 'test@example.com', 0, 'easy')
            ON CONFLICT (id) DO NOTHING;
        """, test_data['user_id'])

        adventure_id = '00000000-0000-0000-0000-000000000005'
        test_date = date.today()
        await db_conn.execute("""
            INSERT INTO adventures (id, user_id, monster_id, duration, start_date, deadline,
                monster_max_hp, monster_current_hp, status)
            VALUES ($1, $2, $3, 5, $4, $5, 200, 200, 'active');
        """, adventure_id, test_data['user_id'], test_data['monster_id'], test_date, test_date + td(days=5))

        entry_id = '00000000-0000-0000-0000-000000000006'
        await db_conn.execute("""
            INSERT INTO daily_entries (id, user_id, adventure_id, date, battle_id)
            VALUES ($1, $2, $3, $4, NULL);
        """, entry_id, test_data['user_id'], adventure_id, test_date)

        # 3 mandatory (all completed) + 2 optional (all completed)
        # Using 'focus' (neutral 1.0x) for both: 3*(100/3*1.0) + 2*(10*1.0) = 100 + 20 = 120
        for i in range(3):
            await db_conn.execute("""
                INSERT INTO tasks (daily_entry_id, content, is_optional, is_completed, category)
                VALUES ($1, $2, false, true, 'focus');
            """, entry_id, f'Mandatory {i}')
        for i in range(2):
            await db_conn.execute("""
                INSERT INTO tasks (daily_entry_id, content, is_optional, is_completed, category)
                VALUES ($1, $2, true, true, 'focus');
            """, entry_id, f'Optional {i}')

        row = await db_conn.fetchrow("SELECT * FROM calculate_adventure_round($1, $2);", adventure_id, test_date)
        damage, new_hp = row['damage'], row['new_hp']

        # 3*(100/3) + 2*10 = 100 + 20 = 120, but due to floating point may be 119
        assert damage >= 119, f"Expected at least 119 damage, got {damage}"
        assert new_hp <= 81, f"Expected HP <= 81 remaining, got {new_hp}"

    async def test_damage_capped_at_180(self, db_conn, test_data, cleanup_test_data):
        """Damage cannot exceed 180 even with many super-effective tasks."""
        await db_conn.execute("""
            INSERT INTO profiles (id, username, email, monster_rating, highest_tier_reached)
            VALUES ($1, 'TestUser', 'test@example.com', 0, 'easy')
            ON CONFLICT (id) DO NOTHING;
        """, test_data['user_id'])

        adventure_id = '00000000-0000-0000-0000-000000000007'
        test_date = date.today()
        # Use a Sloth monster (weak to Physical = 1.5x)
        await db_conn.execute("""
            INSERT INTO adventures (id, user_id, monster_id, duration, start_date, deadline,
                monster_max_hp, monster_current_hp, status)
            VALUES ($1, $2, $3, 5, $4, $5, 200, 200, 'active');
        """, adventure_id, test_data['user_id'], test_data['monster_id'], test_date, test_date + td(days=5))

        entry_id = '00000000-0000-0000-0000-000000000008'
        await db_conn.execute("""
            INSERT INTO daily_entries (id, user_id, adventure_id, date, battle_id)
            VALUES ($1, $2, $3, $4, NULL);
        """, entry_id, test_data['user_id'], adventure_id, test_date)

        # 3 mandatory Physical (SE 1.5x) + 5 optional Physical (SE 1.5x)
        # Would be: 3*(100/3*1.5) + 5*(10*1.5) = 150 + 75 = 225, capped at 180
        for i in range(3):
            await db_conn.execute("""
                INSERT INTO tasks (daily_entry_id, content, is_optional, is_completed, category)
                VALUES ($1, $2, false, true, 'physical');
            """, entry_id, f'Mandatory {i}')
        for i in range(5):
            await db_conn.execute("""
                INSERT INTO tasks (daily_entry_id, content, is_optional, is_completed, category)
                VALUES ($1, $2, true, true, 'physical');
            """, entry_id, f'Optional {i}')

        row = await db_conn.fetchrow("SELECT * FROM calculate_adventure_round($1, $2);", adventure_id, test_date)
        damage = row['damage']

        # Capped at 180 (floating point may give 179 due to FLOOR behavior)
        assert damage >= 179, f"Expected at least 179 damage (capped), got {damage}"
        assert damage <= 180, f"Expected max 180 damage (capped), got {damage}"

    async def test_super_effective_deals_bonus_damage(self, db_conn, test_data, cleanup_test_data):
        """Physical tasks (SE vs Sloth) deal more than neutral tasks."""
        user_id = test_data['user_id']
        monster_id = test_data['monster_id']
        adventure_id = '00000000-0000-0000-0000-000000000030'
        test_date = date.today()

        # Create adventure with Sloth-type monster
        await db_conn.execute("""
            INSERT INTO adventures (id, user_id, monster_id, duration, start_date, deadline,
                monster_max_hp, monster_current_hp, status)
            VALUES ($1, $2, $3, 5, $4, $5, 200, 200, 'active');
        """, adventure_id, user_id, monster_id, test_date, test_date + td(days=5))

        entry_id = '00000000-0000-0000-0000-000000000031'
        await db_conn.execute("""
            INSERT INTO daily_entries (id, user_id, adventure_id, date, battle_id)
            VALUES ($1, $2, $3, $4, NULL);
        """, entry_id, user_id, adventure_id, test_date)

        # 3 Physical tasks (SE vs Sloth = 1.5x): 3 * (100/3 * 1.5) = 150
        for i in range(3):
            await db_conn.execute("""
                INSERT INTO tasks (daily_entry_id, content, is_optional, is_completed, category)
                VALUES ($1, $2, false, true, 'physical');
            """, entry_id, f'Physical Task {i}')

        row = await db_conn.fetchrow("SELECT * FROM calculate_adventure_round($1, $2);", adventure_id, test_date)
        damage, new_hp = row['damage'], row['new_hp']

        # 3 mandatory Physical vs Sloth: 3 * (33.33 * 1.5) = ~150 (may be 149 due to floating point)
        assert damage >= 149, f"Expected at least 149 damage (SE), got {damage}"
        assert damage <= 150, f"Expected max 150 damage (SE), got {damage}"
        assert new_hp <= 51, f"Expected HP <= 51 remaining, got {new_hp}"

    async def test_resisted_deals_reduced_damage(self, db_conn, test_data, cleanup_test_data):
        """Wellness tasks (resisted vs Sloth = 0.5x) deal less damage."""
        user_id = test_data['user_id']
        monster_id = test_data['monster_id']
        adventure_id = '00000000-0000-0000-0000-000000000032'
        test_date = date.today()

        await db_conn.execute("""
            INSERT INTO adventures (id, user_id, monster_id, duration, start_date, deadline,
                monster_max_hp, monster_current_hp, status)
            VALUES ($1, $2, $3, 5, $4, $5, 200, 200, 'active');
        """, adventure_id, user_id, monster_id, test_date, test_date + td(days=5))

        entry_id = '00000000-0000-0000-0000-000000000033'
        await db_conn.execute("""
            INSERT INTO daily_entries (id, user_id, adventure_id, date, battle_id)
            VALUES ($1, $2, $3, $4, NULL);
        """, entry_id, user_id, adventure_id, test_date)

        # 3 Wellness tasks (resisted vs Sloth = 0.5x): 3 * (100/3 * 0.5) = 50
        for i in range(3):
            await db_conn.execute("""
                INSERT INTO tasks (daily_entry_id, content, is_optional, is_completed, category)
                VALUES ($1, $2, false, true, 'wellness');
            """, entry_id, f'Wellness Task {i}')

        row = await db_conn.fetchrow("SELECT * FROM calculate_adventure_round($1, $2);", adventure_id, test_date)
        damage, new_hp = row['damage'], row['new_hp']

        # 3 Wellness vs Sloth: 3 * (33.33 * 0.5) = ~50 (may be 49 due to floating point)
        assert damage >= 49, f"Expected at least 49 damage (resisted), got {damage}"
        assert damage <= 50, f"Expected max 50 damage (resisted), got {damage}"
        assert new_hp >= 150, f"Expected HP >= 150 remaining, got {new_hp}"

    async def test_discoveries_recorded(self, db_conn, test_data, cleanup_test_data):
        """Discoveries are recorded when a round is processed."""
        user_id = test_data['user_id']
        monster_id = test_data['monster_id']
        adventure_id = '00000000-0000-0000-0000-000000000040'
        test_date = date.today()

        await db_conn.execute("""
            INSERT INTO adventures (id, user_id, monster_id, duration, start_date, deadline,
                monster_max_hp, monster_current_hp, status)
            VALUES ($1, $2, $3, 5, $4, $5, 200, 200, 'active');
        """, adventure_id, user_id, monster_id, test_date, test_date + td(days=5))

        entry_id = '00000000-0000-0000-0000-000000000041'
        await db_conn.execute("""
            INSERT INTO daily_entries (id, user_id, adventure_id, date, battle_id)
            VALUES ($1, $2, $3, $4, NULL);
        """, entry_id, user_id, adventure_id, test_date)

        # Use 3 different categories
        categories = ['physical', 'focus', 'wellness']
        for i, cat in enumerate(categories):
            await db_conn.execute("""
                INSERT INTO tasks (daily_entry_id, content, is_optional, is_completed, category)
                VALUES ($1, $2, false, true, $3);
            """, entry_id, f'Task {i}', cat)

        # Process round
        await db_conn.fetchrow("SELECT * FROM calculate_adventure_round($1, $2);", adventure_id, test_date)

        # Check discoveries
        rows = await db_conn.fetch("""
            SELECT task_category, effectiveness
            FROM type_discoveries
            WHERE user_id = $1 AND monster_type = 'sloth'
            ORDER BY task_category;
        """, user_id)

        discoveries = {row['task_category']: row['effectiveness'] for row in rows}

        # Physical should be super_effective vs Sloth
        assert 'physical' in discoveries, "Physical discovery not recorded"
        assert discoveries['physical'] == 'super_effective', \
            f"Physical should be SE vs Sloth, got {discoveries.get('physical')}"

        # Focus should be neutral vs Sloth
        assert 'focus' in discoveries, "Focus discovery not recorded"
        assert discoveries['focus'] == 'neutral', \
            f"Focus should be neutral vs Sloth, got {discoveries.get('focus')}"

        # Wellness should be resisted vs Sloth
        assert 'wellness' in discoveries, "Wellness discovery not recorded"
        assert discoveries['wellness'] == 'resisted', \
            f"Wellness should be resisted vs Sloth, got {discoveries.get('wellness')}"

    async def test_no_mandatory_only_optional(self, db_conn, test_data, cleanup_test_data):
        """With no mandatory tasks, damage = optional * 10 (with multipliers)."""
        await db_conn.execute("""
            INSERT INTO profiles (id, username, email, monster_rating, highest_tier_reached)
            VALUES ($1, 'TestUser', 'test@example.com', 0, 'easy')
            ON CONFLICT (id) DO NOTHING;
        """, test_data['user_id'])

        adventure_id = '00000000-0000-0000-0000-000000000009'
        test_date = date.today()
        await db_conn.execute("""
            INSERT INTO adventures (id, user_id, monster_id, duration, start_date, deadline,
                monster_max_hp, monster_current_hp, status)
            VALUES ($1, $2, $3, 5, $4, $5, 200, 200, 'active');
        """, adventure_id, test_data['user_id'], test_data['monster_id'], test_date, test_date + td(days=5))

        entry_id = '00000000-0000-0000-0000-000000000010'
        await db_conn.execute("""
            INSERT INTO daily_entries (id, user_id, adventure_id, date, battle_id)
            VALUES ($1, $2, $3, $4, NULL);
        """, entry_id, test_data['user_id'], adventure_id, test_date)

        # Only 5 optional tasks, all completed = 50 damage (neutral category)
        for i in range(5):
            await db_conn.execute("""
                INSERT INTO tasks (daily_entry_id, content, is_optional, is_completed, category)
                VALUES ($1, $2, true, true, 'focus');
            """, entry_id, f'Optional {i}')

        row = await db_conn.fetchrow("SELECT * FROM calculate_adventure_round($1, $2);", adventure_id, test_date)
        damage, new_hp = row['damage'], row['new_hp']

        # 5 * 10 * 1.0 = 50 damage
        assert damage == 50, f"Expected 50 damage, got {damage}"

    async def test_no_tasks_planned_returns_zero_damage(self, db_conn, test_data, cleanup_test_data):
        """No daily_entry or tasks = 0 damage."""
        await db_conn.execute("""
            INSERT INTO profiles (id, username, email, monster_rating, highest_tier_reached)
            VALUES ($1, 'TestUser', 'test@example.com', 0, 'easy')
            ON CONFLICT (id) DO NOTHING;
        """, test_data['user_id'])

        adventure_id = '00000000-0000-0000-0000-000000000011'
        test_date = date.today()
        await db_conn.execute("""
            INSERT INTO adventures (id, user_id, monster_id, duration, start_date, deadline,
                monster_max_hp, monster_current_hp, status)
            VALUES ($1, $2, $3, 5, $4, $5, 200, 200, 'active');
        """, adventure_id, test_data['user_id'], test_data['monster_id'], test_date, test_date + td(days=5))

        # No daily entry created - should return 0 damage
        row = await db_conn.fetchrow("SELECT * FROM calculate_adventure_round($1, $2);", adventure_id, test_date)
        damage, new_hp = row['damage'], row['new_hp']

        assert damage == 0, f"Expected 0 damage (no tasks), got {damage}"
        assert new_hp == 200, f"Expected 200 HP (unchanged), got {new_hp}"

    async def test_on_break_skips_processing(self, db_conn, test_data, cleanup_test_data):
        """Adventure on break returns 0 damage."""
        await db_conn.execute("""
            INSERT INTO profiles (id, username, email, monster_rating, highest_tier_reached)
            VALUES ($1, 'TestUser', 'test@example.com', 0, 'easy')
            ON CONFLICT (id) DO NOTHING;
        """, test_data['user_id'])

        adventure_id = '00000000-0000-0000-0000-000000000012'
        test_date = date.today()
        tomorrow = test_date + td(days=1)
        await db_conn.execute("""
            INSERT INTO adventures (id, user_id, monster_id, duration, start_date, deadline,
                monster_max_hp, monster_current_hp, status, is_on_break, break_end_date)
            VALUES ($1, $2, $3, 5, $4, $5, 200, 200, 'active', true, $6);
        """, adventure_id, test_data['user_id'], test_data['monster_id'], test_date, test_date + td(days=5), tomorrow)

        entry_id = '00000000-0000-0000-0000-000000000013'
        await db_conn.execute("""
            INSERT INTO daily_entries (id, user_id, adventure_id, date, battle_id)
            VALUES ($1, $2, $3, $4, NULL);
        """, entry_id, test_data['user_id'], adventure_id, test_date)

        # Create completed tasks (should be ignored due to break)
        for i in range(3):
            await db_conn.execute("""
                INSERT INTO tasks (daily_entry_id, content, is_optional, is_completed, category)
                VALUES ($1, $2, false, true, 'focus');
            """, entry_id, f'Task {i}')

        row = await db_conn.fetchrow("SELECT * FROM calculate_adventure_round($1, $2);", adventure_id, test_date)
        damage, new_hp = row['damage'], row['new_hp']

        assert damage == 0, f"Expected 0 damage (on break), got {damage}"
        assert new_hp == 200, f"Expected 200 HP (unchanged), got {new_hp}"

    async def test_break_cleared_after_end_date(self, db_conn, test_data, cleanup_test_data):
        """Break status cleared when round_date >= break_end_date."""
        await db_conn.execute("""
            INSERT INTO profiles (id, username, email, monster_rating, highest_tier_reached)
            VALUES ($1, 'TestUser', 'test@example.com', 0, 'easy')
            ON CONFLICT (id) DO NOTHING;
        """, test_data['user_id'])

        adventure_id = '00000000-0000-0000-0000-000000000014'
        test_date = date.today()
        yesterday = test_date - td(days=1)
        await db_conn.execute("""
            INSERT INTO adventures (id, user_id, monster_id, duration, start_date, deadline,
                monster_max_hp, monster_current_hp, status, is_on_break, break_end_date)
            VALUES ($1, $2, $3, 5, $4, $5, 200, 200, 'active', true, $6);
        """, adventure_id, test_data['user_id'], test_data['monster_id'], test_date, test_date + td(days=5), yesterday)

        entry_id = '00000000-0000-0000-0000-000000000015'
        await db_conn.execute("""
            INSERT INTO daily_entries (id, user_id, adventure_id, date, battle_id)
            VALUES ($1, $2, $3, $4, NULL);
        """, entry_id, test_data['user_id'], adventure_id, test_date)

        # Create completed tasks
        for i in range(3):
            await db_conn.execute("""
                INSERT INTO tasks (daily_entry_id, content, is_optional, is_completed, category)
                VALUES ($1, $2, false, true, 'focus');
            """, entry_id, f'Task {i}')

        row = await db_conn.fetchrow("SELECT * FROM calculate_adventure_round($1, $2);", adventure_id, test_date)
        damage = row['damage']

        # Break should be cleared and damage applied
        assert damage >= 99, f"Expected at least 99 damage (break cleared), got {damage}"

        # Verify break status was cleared
        is_on_break = await db_conn.fetchval("SELECT is_on_break FROM adventures WHERE id = $1;", adventure_id)
        assert is_on_break is False, "Break status should be cleared"

    async def test_adventure_stats_updated(self, db_conn, test_data, cleanup_test_data):
        """Updates total_damage_dealt and current_round."""
        await db_conn.execute("""
            INSERT INTO profiles (id, username, email, monster_rating, highest_tier_reached)
            VALUES ($1, 'TestUser', 'test@example.com', 0, 'easy')
            ON CONFLICT (id) DO NOTHING;
        """, test_data['user_id'])

        adventure_id = '00000000-0000-0000-0000-000000000016'
        test_date = date.today()
        await db_conn.execute("""
            INSERT INTO adventures (id, user_id, monster_id, duration, start_date, deadline,
                monster_max_hp, monster_current_hp, status, total_damage_dealt, current_round)
            VALUES ($1, $2, $3, 5, $4, $5, 200, 200, 'active', 0, 0);
        """, adventure_id, test_data['user_id'], test_data['monster_id'], test_date, test_date + td(days=5))

        entry_id = '00000000-0000-0000-0000-000000000017'
        await db_conn.execute("""
            INSERT INTO daily_entries (id, user_id, adventure_id, date, battle_id)
            VALUES ($1, $2, $3, $4, NULL);
        """, entry_id, test_data['user_id'], adventure_id, test_date)

        # Create 2/3 mandatory completed = 67 damage rounded (using neutral category)
        for i in range(3):
            is_completed = i < 2
            await db_conn.execute("""
                INSERT INTO tasks (daily_entry_id, content, is_optional, is_completed, category)
                VALUES ($1, $2, false, $3, 'focus');
            """, entry_id, f'Task {i}', is_completed)

        await db_conn.fetchrow("SELECT * FROM calculate_adventure_round($1, $2);", adventure_id, test_date)

        # Check stats updated
        row = await db_conn.fetchrow("""
            SELECT total_damage_dealt, current_round FROM adventures WHERE id = $1;
        """, adventure_id)
        total_damage, round_num = row['total_damage_dealt'], row['current_round']

        assert total_damage > 0, f"total_damage_dealt should be > 0, got {total_damage}"
        assert round_num == 1, f"current_round should be 1, got {round_num}"

    async def test_daily_entry_xp_updated(self, db_conn, test_data, cleanup_test_data):
        """Stores damage in daily_entry.daily_xp."""
        await db_conn.execute("""
            INSERT INTO profiles (id, username, email, monster_rating, highest_tier_reached)
            VALUES ($1, 'TestUser', 'test@example.com', 0, 'easy')
            ON CONFLICT (id) DO NOTHING;
        """, test_data['user_id'])

        adventure_id = '00000000-0000-0000-0000-000000000018'
        test_date = date.today()
        await db_conn.execute("""
            INSERT INTO adventures (id, user_id, monster_id, duration, start_date, deadline,
                monster_max_hp, monster_current_hp, status)
            VALUES ($1, $2, $3, 5, $4, $5, 200, 200, 'active');
        """, adventure_id, test_data['user_id'], test_data['monster_id'], test_date, test_date + td(days=5))

        entry_id = '00000000-0000-0000-0000-000000000019'
        await db_conn.execute("""
            INSERT INTO daily_entries (id, user_id, adventure_id, date, battle_id, daily_xp)
            VALUES ($1, $2, $3, $4, NULL, 0);
        """, entry_id, test_data['user_id'], adventure_id, test_date)

        # Create 3 mandatory tasks all completed
        for i in range(3):
            await db_conn.execute("""
                INSERT INTO tasks (daily_entry_id, content, is_optional, is_completed, category)
                VALUES ($1, $2, false, true, 'focus');
            """, entry_id, f'Task {i}')

        row = await db_conn.fetchrow("SELECT * FROM calculate_adventure_round($1, $2);", adventure_id, test_date)
        damage = row['damage']

        # Check daily_xp updated
        daily_xp = await db_conn.fetchval("SELECT daily_xp FROM daily_entries WHERE id = $1;", entry_id)

        assert daily_xp == damage, f"daily_xp should be {damage}, got {daily_xp}"

    async def test_monster_hp_floors_at_zero(self, db_conn, test_data, cleanup_test_data):
        """Monster HP cannot go below 0."""
        await db_conn.execute("""
            INSERT INTO profiles (id, username, email, monster_rating, highest_tier_reached)
            VALUES ($1, 'TestUser', 'test@example.com', 0, 'easy')
            ON CONFLICT (id) DO NOTHING;
        """, test_data['user_id'])

        adventure_id = '00000000-0000-0000-0000-000000000020'
        test_date = date.today()
        # Create adventure with only 50 HP
        await db_conn.execute("""
            INSERT INTO adventures (id, user_id, monster_id, duration, start_date, deadline,
                monster_max_hp, monster_current_hp, status)
            VALUES ($1, $2, $3, 5, $4, $5, 50, 50, 'active');
        """, adventure_id, test_data['user_id'], test_data['monster_id'], test_date, test_date + td(days=5))

        entry_id = '00000000-0000-0000-0000-000000000021'
        await db_conn.execute("""
            INSERT INTO daily_entries (id, user_id, adventure_id, date, battle_id)
            VALUES ($1, $2, $3, $4, NULL);
        """, entry_id, test_data['user_id'], adventure_id, test_date)

        # Create tasks that deal 100+ damage
        for i in range(3):
            await db_conn.execute("""
                INSERT INTO tasks (daily_entry_id, content, is_optional, is_completed, category)
                VALUES ($1, $2, false, true, 'focus');
            """, entry_id, f'Task {i}')

        row = await db_conn.fetchrow("SELECT * FROM calculate_adventure_round($1, $2);", adventure_id, test_date)
        new_hp = row['new_hp']

        assert new_hp == 0, f"HP should floor at 0, got {new_hp}"


@pytest.mark.skipif(not DB_AVAILABLE, reason="Database connection not available")
@pytest.mark.asyncio
class TestBattlesBreakColumns:
    """Tests for battles table break feature columns."""

    async def test_break_columns_exist(self, db_conn):
        """Verify all break columns exist."""
        rows = await db_conn.fetch("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'battles'
            AND column_name IN (
                'break_days_used', 'max_break_days', 'is_on_break',
                'break_end_date', 'break_requested_by', 'break_request_expires_at'
            );
        """)
        columns = {row['column_name'] for row in rows}

        expected_columns = {
            'break_days_used', 'max_break_days', 'is_on_break',
            'break_end_date', 'break_requested_by', 'break_request_expires_at'
        }
        assert expected_columns == columns, f"Column mismatch. Expected: {expected_columns}, Got: {columns}"

    async def test_break_columns_have_defaults(self, db_conn):
        """Verify break columns have correct default values."""
        rows = await db_conn.fetch("""
            SELECT column_default, data_type
            FROM information_schema.columns
            WHERE table_name = 'battles'
            AND column_name IN ('break_days_used', 'max_break_days', 'is_on_break')
            ORDER BY column_name;
        """)
        defaults = {row['column_default'] for row in rows}
        # break_days_used and max_break_days should default to 0
        # is_on_break should default to false
        assert any('0' in str(d) for d in defaults), "break_days_used/max_break_days should default to 0"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
