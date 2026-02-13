"""
End-to-End tests for Adventure API with real database.

These tests:
- Make real HTTP requests via FastAPI TestClient
- Use real PostgreSQL database connections
- Create/read/delete real data
- Verify SQL functions work correctly
- Test the complete flow from HTTP request to database

Prerequisites:
- Database connection configured (.env file)
- Test user exists: 80c0d05e-e927-4860-a17e-8bb085df6fbb
- Monsters are seeded in database
- SQL functions are deployed

Run with:
    pytest tests/integration/test_adventures_e2e.py -v
"""
import pytest
import sys
import os
from datetime import date, timedelta
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from main import app
from dependencies import get_current_user
from database import get_db_connection, return_db_connection, supabase

# =============================================================================
# Configuration
# =============================================================================

TEST_USER_ID = "80c0d05e-e927-4860-a17e-8bb085df6fbb"


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture(scope='module')
def db_connection():
    """Get real database connection."""
    conn = get_db_connection()
    if not conn:
        pytest.skip("Database connection not available")
    yield conn
    return_db_connection(conn)


@pytest.fixture
def client():
    """Create TestClient."""
    return TestClient(app)


@pytest.fixture
def authenticated_client(client):
    """Create TestClient with authentication override."""
    mock_user = Mock()
    mock_user.id = TEST_USER_ID
    app.dependency_overrides[get_current_user] = lambda: mock_user
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def cleanup_test_data(db_connection):
    """Cleanup test adventures before and after each test."""
    cursor = db_connection.cursor()
    try:
        # Cleanup before test
        cursor.execute("UPDATE profiles SET current_adventure = NULL WHERE id = %s;", (TEST_USER_ID,))
        cursor.execute("DELETE FROM tasks WHERE daily_entry_id IN (SELECT id FROM daily_entries WHERE user_id = %s);", (TEST_USER_ID,))
        cursor.execute("DELETE FROM daily_entries WHERE user_id = %s;", (TEST_USER_ID,))
        cursor.execute("DELETE FROM adventures WHERE user_id = %s;", (TEST_USER_ID,))
        db_connection.commit()
    except Exception as e:
        db_connection.rollback()
        print(f"Cleanup error: {e}")

    yield

    # Cleanup after test
    try:
        cursor.execute("UPDATE profiles SET current_adventure = NULL WHERE id = %s;", (TEST_USER_ID,))
        cursor.execute("DELETE FROM tasks WHERE daily_entry_id IN (SELECT id FROM daily_entries WHERE user_id = %s);", (TEST_USER_ID,))
        cursor.execute("DELETE FROM daily_entries WHERE user_id = %s;", (TEST_USER_ID,))
        cursor.execute("DELETE FROM adventures WHERE user_id = %s;", (TEST_USER_ID,))
        db_connection.commit()
    except Exception as e:
        db_connection.rollback()
        print(f"Cleanup error: {e}")
    finally:
        cursor.close()


@pytest.fixture
def easy_monster_id(db_connection):
    """Get a real easy monster ID from database."""
    cursor = db_connection.cursor()
    try:
        cursor.execute("SELECT id FROM monsters WHERE tier = 'easy' LIMIT 1;")
        result = cursor.fetchone()
        if not result:
            pytest.skip("No easy monsters found in database")
        return result[0]
    finally:
        cursor.close()


@pytest.fixture
def verify_monsters_seeded(db_connection):
    """Verify monsters table is seeded."""
    cursor = db_connection.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM monsters;")
        result = cursor.fetchone()
        if not result or result[0] == 0:
            pytest.skip("Monsters table is empty. Run seed_monsters.sql first.")
    finally:
        cursor.close()


# =============================================================================
# Test GET /api/adventures/monsters (E2E)
# =============================================================================

@pytest.mark.e2e
class TestGetMonstersE2E:
    """End-to-end tests for GET /api/adventures/monsters."""

    def test_returns_real_monsters_from_db(self, authenticated_client, verify_monsters_seeded, db_connection):
        """Verify endpoint returns actual monsters from database."""
        # Get user's actual rating
        cursor = db_connection.cursor()
        cursor.execute("SELECT monster_rating FROM profiles WHERE id = %s;", (TEST_USER_ID,))
        result = cursor.fetchone()
        cursor.close()

        if not result:
            pytest.skip("Test user not found in profiles table")

        rating = result[0] or 0

        response = authenticated_client.get("/api/adventures/monsters")

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert 'monsters' in data
        assert 'refreshes_remaining' in data
        assert 'unlocked_tiers' in data
        assert 'current_rating' in data

        # Verify we got monsters
        assert len(data['monsters']) > 0, "Should return at least one monster"
        assert len(data['monsters']) <= 4, "Should return at most 4 monsters"

        # Verify monster structure
        monster = data['monsters'][0]
        assert 'id' in monster
        assert 'name' in monster
        assert 'tier' in monster
        assert 'base_hp' in monster

        # Verify monster IDs are real (UUIDs)
        assert len(monster['id']) == 36, "Monster ID should be a UUID"

    def test_monsters_belong_to_unlocked_tiers(self, authenticated_client, verify_monsters_seeded, db_connection):
        """Verify returned monsters match user's unlocked tiers."""
        # Get user's rating
        cursor = db_connection.cursor()
        cursor.execute("SELECT monster_rating FROM profiles WHERE id = %s;", (TEST_USER_ID,))
        result = cursor.fetchone()
        cursor.close()

        rating = result[0] or 0
        unlocked_tiers = []
        if rating >= 0:
            unlocked_tiers.append('easy')
        if rating >= 2:
            unlocked_tiers.append('medium')
        if rating >= 5:
            unlocked_tiers.append('hard')
        if rating >= 9:
            unlocked_tiers.append('expert')
        if rating >= 14:
            unlocked_tiers.append('boss')

        response = authenticated_client.get("/api/adventures/monsters")
        assert response.status_code == 200

        data = response.json()
        returned_tiers = {m['tier'] for m in data['monsters']}

        # All returned monsters should be from unlocked tiers
        for tier in returned_tiers:
            assert tier in unlocked_tiers, f"Tier {tier} not unlocked for rating {rating}"


# =============================================================================
# Test POST /api/adventures/start (E2E)
# =============================================================================

@pytest.mark.e2e
class TestStartAdventureE2E:
    """End-to-end tests for POST /api/adventures/start."""

    def test_creates_real_adventure_in_db(self, authenticated_client, cleanup_test_data, easy_monster_id, db_connection):
        """Verify starting an adventure creates real database row."""
        monster_id = easy_monster_id

        # Start adventure
        response = authenticated_client.post("/api/adventures/start", json={"monster_id": monster_id})

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert 'id' in data
        assert 'user_id' in data
        assert 'monster_id' in data
        assert data['user_id'] == TEST_USER_ID
        assert data['monster_id'] == monster_id
        assert data['status'] == 'active'

        adventure_id = data['id']

        # Verify in database
        cursor = db_connection.cursor()
        try:
            cursor.execute("SELECT * FROM adventures WHERE id = %s;", (adventure_id,))
            result = cursor.fetchone()
            assert result is not None, "Adventure not found in database"

            # Verify profile was updated
            cursor.execute("SELECT current_adventure FROM profiles WHERE id = %s;", (TEST_USER_ID,))
            profile_result = cursor.fetchone()
            assert profile_result is not None
            assert profile_result[0] == adventure_id, "Profile's current_adventure not updated"
        finally:
            cursor.close()

    def test_prevents_duplicate_adventures(self, authenticated_client, cleanup_test_data, easy_monster_id):
        """Verify cannot start adventure when one is already active."""
        monster_id = easy_monster_id

        # Start first adventure
        response1 = authenticated_client.post("/api/adventures/start", json={"monster_id": monster_id})
        assert response1.status_code == 200, "First adventure should start"

        # Try to start second adventure
        response2 = authenticated_client.post("/api/adventures/start", json={"monster_id": monster_id})
        assert response2.status_code == 400, "Should not allow duplicate adventure"

    def test_validates_tier_access(self, authenticated_client, cleanup_test_data, db_connection):
        """Verify cannot select monster from locked tier."""
        cursor = db_connection.cursor()
        try:
            # Ensure user has low rating
            cursor.execute("UPDATE profiles SET monster_rating = 0 WHERE id = %s;", (TEST_USER_ID,))
            db_connection.commit()

            # Get a boss monster (should be locked)
            cursor.execute("SELECT id FROM monsters WHERE tier = 'boss' LIMIT 1;")
            result = cursor.fetchone()
            if not result:
                pytest.skip("No boss monsters found")
            boss_monster_id = result[0]
        finally:
            cursor.close()

        # Try to start with boss monster
        response = authenticated_client.post("/api/adventures/start", json={"monster_id": boss_monster_id})

        assert response.status_code == 403, "Should be forbidden to select locked tier"


# =============================================================================
# Test GET /api/adventures/current (E2E)
# =============================================================================

@pytest.mark.e2e
class TestGetCurrentAdventureE2E:
    """End-to-end tests for GET /api/adventures/current."""

    @pytest.fixture
    def active_adventure(self, authenticated_client, cleanup_test_data, easy_monster_id):
        """Create an active adventure for testing."""
        response = authenticated_client.post("/api/adventures/start", json={"monster_id": easy_monster_id})
        assert response.status_code == 200
        return response.json()

    def test_returns_active_adventure_with_real_data(self, authenticated_client, active_adventure):
        """Verify current adventure returns real data from database."""
        response = authenticated_client.get("/api/adventures/current")

        assert response.status_code == 200
        data = response.json()

        # Verify structure
        assert 'id' in data
        assert 'status' in data
        assert 'app_state' in data
        assert 'days_remaining' in data
        assert 'monster' in data

        # Verify app_state is one of the expected values
        valid_states = ['ACTIVE', 'ON_BREAK', 'PRE_ADVENTURE', 'LAST_DAY', 'DEADLINE_PASSED']
        assert data['app_state'] in valid_states

    def test_includes_monster_details(self, authenticated_client, active_adventure):
        """Verify monster data is included."""
        response = authenticated_client.get("/api/adventures/current")

        assert response.status_code == 200
        data = response.json()

        monster = data.get('monster')
        assert monster is not None
        assert 'name' in monster
        assert 'tier' in monster
        assert 'base_hp' in monster

    def test_returns_404_when_no_active_adventure(self, authenticated_client, cleanup_test_data):
        """Verify 404 when user has no active adventure."""
        # Ensure no adventure exists
        response = authenticated_client.get("/api/adventures/current")
        assert response.status_code == 404


# =============================================================================
# Test POST /api/adventures/{id}/break (E2E)
# =============================================================================

@pytest.mark.e2e
class TestScheduleBreakE2E:
    """End-to-end tests for POST /api/adventures/{id}/break."""

    @pytest.fixture
    def active_adventure(self, authenticated_client, cleanup_test_data, easy_monster_id, db_connection):
        """Create an active adventure for testing."""
        response = authenticated_client.post("/api/adventures/start", json={"monster_id": easy_monster_id})
        assert response.status_code == 200
        return response.json()

    def test_schedules_break_in_db(self, authenticated_client, active_adventure, db_connection):
        """Verify scheduling break updates database correctly."""
        adventure_id = active_adventure['id']
        original_deadline = active_adventure['deadline']

        response = authenticated_client.post(f"/api/adventures/{adventure_id}/break")

        assert response.status_code == 200
        data = response.json()

        assert data['status'] == 'break_scheduled'
        assert 'break_date' in data
        assert 'new_deadline' in data
        assert 'breaks_remaining' in data

        # Verify in database
        cursor = db_connection.cursor()
        try:
            cursor.execute("SELECT is_on_break, break_days_used, deadline FROM adventures WHERE id = %s;", (adventure_id,))
            result = cursor.fetchone()
            assert result is not None

            is_on_break, breaks_used, deadline = result
            assert is_on_break == True
            assert breaks_used == 1
            # Deadline should be extended by 1 day
            assert deadline != original_deadline
        finally:
            cursor.close()

    def test_respects_max_break_limit(self, authenticated_client, active_adventure, db_connection):
        """Verify cannot exceed max break days."""
        adventure_id = active_adventure['id']

        # Schedule first break
        response1 = authenticated_client.post(f"/api/adventures/{adventure_id}/break")
        assert response1.status_code == 200

        # Clear the break status (simulate day passing)
        cursor = db_connection.cursor()
        try:
            cursor.execute("UPDATE adventures SET is_on_break = FALSE, break_end_date = NULL WHERE id = %s;", (adventure_id,))
            db_connection.commit()
        finally:
            cursor.close()

        # Schedule second break
        response2 = authenticated_client.post(f"/api/adventures/{adventure_id}/break")
        assert response2.status_code == 200

        # Clear break again
        cursor = db_connection.cursor()
        try:
            cursor.execute("UPDATE adventures SET is_on_break = FALSE, break_end_date = NULL WHERE id = %s;", (adventure_id,))
            db_connection.commit()
        finally:
            cursor.close()

        # Third try should fail
        response3 = authenticated_client.post(f"/api/adventures/{adventure_id}/break")
        assert response3.status_code == 400


# =============================================================================
# Test POST /api/adventures/{id}/abandon (E2E)
# =============================================================================

@pytest.mark.e2e
class TestAbandonAdventureE2E:
    """End-to-end tests for POST /api/adventures/{id}/abandon."""

    @pytest.fixture
    def active_adventure(self, authenticated_client, cleanup_test_data, easy_monster_id):
        """Create an active adventure for testing."""
        response = authenticated_client.post("/api/adventures/start", json={"monster_id": easy_monster_id})
        assert response.status_code == 200
        return response.json()

    def test_abandons_adventure_with_partial_xp(self, authenticated_client, active_adventure, db_connection):
        """Verify abandoning calculates 50% XP correctly."""
        adventure_id = active_adventure['id']

        # Deal some damage first (but leave HP > 0)
        cursor = db_connection.cursor()
        try:
            cursor.execute("UPDATE adventures SET total_damage_dealt = 200, monster_current_hp = 50 WHERE id = %s;", (adventure_id,))
            db_connection.commit()
        finally:
            cursor.close()

        response = authenticated_client.post(f"/api/adventures/{adventure_id}/abandon")

        assert response.status_code == 200
        data = response.json()

        assert 'status' in data
        assert 'xp_earned' in data

        # Verify in database
        cursor = db_connection.cursor()
        try:
            cursor.execute("SELECT status, xp_earned FROM adventures WHERE id = %s;", (adventure_id,))
            result = cursor.fetchone()
            assert result is not None

            status, xp = result
            # When monster escapes (HP > 0), status is 'escaped'
            assert status == 'escaped'
            assert xp > 0, "Should have earned some XP"
        finally:
            cursor.close()

    def test_clears_profile_current_adventure(self, authenticated_client, active_adventure, db_connection):
        """Verify abandoning clears profile's current_adventure."""
        adventure_id = active_adventure['id']

        response = authenticated_client.post(f"/api/adventures/{adventure_id}/abandon")
        assert response.status_code == 200

        # Verify profile was cleared
        cursor = db_connection.cursor()
        try:
            cursor.execute("SELECT current_adventure FROM profiles WHERE id = %s;", (TEST_USER_ID,))
            result = cursor.fetchone()
            assert result is not None
            assert result[0] is None, "Profile's current_adventure should be cleared after abandon"
        finally:
            cursor.close()


# =============================================================================
# Test SQL Functions (E2E)
# =============================================================================

@pytest.mark.e2e
class TestSQLFunctionsE2E:
    """End-to-end tests that verify SQL functions work through the API."""

    @pytest.fixture
    def adventure_with_entries(self, authenticated_client, cleanup_test_data, easy_monster_id, db_connection):
        """Create an adventure with daily entries for testing round processing."""
        # Start adventure
        response = authenticated_client.post("/api/adventures/start", json={"monster_id": easy_monster_id})
        assert response.status_code == 200
        adventure = response.json()

        # Create a daily entry with some damage
        cursor = db_connection.cursor()
        try:
            cursor.execute("""
                INSERT INTO daily_entries (user_id, adventure_id, date, daily_xp, is_locked)
                VALUES (%s, %s, %s, 100, true)
                RETURNING id;
            """, (TEST_USER_ID, adventure['id'], date.today()))
            entry_id = cursor.fetchone()[0]
            db_connection.commit()

            adventure['entry_id'] = entry_id
        finally:
            cursor.close()

        return adventure

    def test_calculate_adventure_round_function_works(self, authenticated_client, adventure_with_entries, db_connection):
        """Verify calculate_adventure_round SQL function processes correctly."""
        adventure_id = adventure_with_entries['id']

        # Call the SQL function directly
        cursor = db_connection.cursor()
        try:
            cursor.execute("""
                SELECT * FROM calculate_adventure_round(
                    adventure_uuid := %s,
                    round_date := %s
                );
            """, (adventure_id, date.today().isoformat()))

            result = cursor.fetchone()
            assert result is not None, "SQL function should return result"

            # Result should contain: damage_dealt, monster_died, adventure_completed
            # The exact structure depends on the function's return type
            print(f"calculate_adventure_round result: {result}")
        finally:
            cursor.close()

    def test_complete_adventure_function_works(self, authenticated_client, adventure_with_entries, db_connection):
        """Verify complete_adventure SQL function works."""
        adventure_id = adventure_with_entries['id']

        # First deal max damage to ensure monster dies
        cursor = db_connection.cursor()
        try:
            cursor.execute("UPDATE adventures SET monster_current_hp = 0 WHERE id = %s;", (adventure_id,))
            db_connection.commit()
        finally:
            cursor.close()

        # Call the complete function
        cursor = db_connection.cursor()
        try:
            cursor.execute("SELECT * FROM complete_adventure(adventure_uuid := %s);", (adventure_id,))
            result = cursor.fetchone()
            assert result is not None, "complete_adventure should return result"
            print(f"complete_adventure result: {result}")

            # Verify adventure is completed
            cursor.execute("SELECT status FROM adventures WHERE id = %s;", (adventure_id,))
            status_result = cursor.fetchone()
            assert status_result[0] in ['completed', 'victory']
        finally:
            cursor.close()


# =============================================================================
# Test Complete Flow (E2E)
# =============================================================================

@pytest.mark.e2e
class TestCompleteAdventureFlow:
    """Test the complete adventure flow from start to finish."""

    def test_full_adventure_lifecycle(self, authenticated_client, cleanup_test_data, easy_monster_id, db_connection):
        """Test complete adventure: start → check current → abandon."""
        # 1. Start adventure
        start_response = authenticated_client.post("/api/adventures/start", json={"monster_id": easy_monster_id})
        assert start_response.status_code == 200
        adventure = start_response.json()
        adventure_id = adventure['id']

        # 2. Get current adventure
        current_response = authenticated_client.get("/api/adventures/current")
        assert current_response.status_code == 200
        current_data = current_response.json()
        assert current_data['id'] == adventure_id
        assert current_data['status'] == 'active'

        # 3. Deal some damage (simulate task completion)
        cursor = db_connection.cursor()
        try:
            cursor.execute("UPDATE adventures SET total_damage_dealt = 150, monster_current_hp = 50 WHERE id = %s;", (adventure_id,))
            db_connection.commit()
        finally:
            cursor.close()

        # 4. Get adventure details
        details_response = authenticated_client.get(f"/api/adventures/{adventure_id}")
        assert details_response.status_code == 200
        details_data = details_response.json()
        assert details_data['total_damage_dealt'] == 150

        # 5. Abandon adventure
        abandon_response = authenticated_client.post(f"/api/adventures/{adventure_id}/abandon")
        assert abandon_response.status_code == 200
        abandon_data = abandon_response.json()
        assert 'xp_earned' in abandon_data

        # 6. Verify cleanup in database
        cursor = db_connection.cursor()
        try:
            cursor.execute("SELECT current_adventure FROM profiles WHERE id = %s;", (TEST_USER_ID,))
            profile_result = cursor.fetchone()
            assert profile_result[0] is None, "Profile should have no current adventure after abandon"

            cursor.execute("SELECT status FROM adventures WHERE id = %s;", (adventure_id,))
            adventure_result = cursor.fetchone()
            # When abandoning with HP remaining, status is 'escaped'
            assert adventure_result[0] in ['abandoned', 'escaped']
        finally:
            cursor.close()


# =============================================================================
# Test Complete Adventure Victory Flows (E2E)
# =============================================================================

@pytest.mark.e2e
class TestAdventureVictoryFlow:
    """End-to-end tests for complete adventure victory cycles."""

    def test_quick_victory_two_round_kill(self, authenticated_client, cleanup_test_data, db_connection):
        """Full victory cycle: kill a low-HP easy monster in 2 rounds.

        Scenario:
        1. Start adventure with easy monster (100-200 HP)
        2. Day 1: Plan and complete tasks dealing ~80 damage
        3. Day 2: Plan and complete remaining tasks to finish off monster
        4. Complete adventure with victory
        5. Verify profile stats updated correctly (defeats++, rating++, XP granted)
        """
        cursor = db_connection.cursor()
        try:
            # Get a low-HP easy monster (Lazy Slime has 100 HP)
            cursor.execute("SELECT id, base_hp FROM monsters WHERE tier = 'easy' ORDER BY base_hp ASC LIMIT 1;")
            result = cursor.fetchone()
            if not result:
                pytest.skip("No easy monsters found")
            monster_id, monster_hp = result

            # Reset user stats for clean test
            cursor.execute("""
                UPDATE profiles SET
                    adventure_count = 0,
                    monster_defeats = 0,
                    monster_escapes = 0,
                    monster_rating = 0,
                    highest_tier_reached = 'easy',
                    current_adventure = NULL
                WHERE id = %s;
            """, (TEST_USER_ID,))
            db_connection.commit()

            # Step 1: Start adventure
            start_response = authenticated_client.post("/api/adventures/start", json={"monster_id": monster_id})
            assert start_response.status_code == 200
            adventure = start_response.json()
            adventure_id = adventure['id']

            # Verify initial state
            assert adventure['status'] == 'active'
            assert adventure['monster_current_hp'] == monster_hp
            assert adventure['total_damage_dealt'] == 0
            assert adventure['current_round'] == 0

            # Step 2: Day 1 - Draft and complete tasks (deal ~80% damage)
            today = date.today()
            day1 = today.isoformat()

            # Create daily entry for day 1 with 3 mandatory tasks (all completed)
            # Using 'focus' category (neutral vs Sloth = 1.0x)
            # 3 mandatory tasks completed = 100 damage
            cursor.execute("""
                INSERT INTO daily_entries (user_id, adventure_id, date, daily_xp, is_locked)
                VALUES (%s, %s, %s, 0, true)
                RETURNING id;
            """, (TEST_USER_ID, adventure_id, day1))
            entry1_id = cursor.fetchone()[0]

            # Insert 3 completed mandatory focus tasks
            for i in range(3):
                cursor.execute("""
                    INSERT INTO tasks (daily_entry_id, content, is_optional, is_completed, category)
                    VALUES (%s, %s, false, true, 'focus');
                """, (entry1_id, f"Day 1 Focus Task {i+1}"))
            db_connection.commit()

            # Process Day 1 round
            cursor.execute("SELECT * FROM calculate_adventure_round(%s, %s);", (adventure_id, day1))
            round1_result = cursor.fetchone()
            damage1, new_hp1 = round1_result
            db_connection.commit()

            # Verify Day 1 damage
            assert damage1 >= 99, f"Day 1 damage should be ~100, got {damage1}"
            assert new_hp1 < monster_hp, f"Monster HP should decrease, got {new_hp1}"

            # Check adventure state after round 1
            cursor.execute("""
                SELECT monster_current_hp, total_damage_dealt, current_round
                FROM adventures WHERE id = %s;
            """, (adventure_id,))
            hp1, total1, round1_num = cursor.fetchone()
            assert round1_num == 1
            assert total1 == damage1

            # Step 3: Day 2 - Finish off monster
            day2 = (today + timedelta(days=1)).isoformat()

            # Create daily entry for day 2
            cursor.execute("""
                INSERT INTO daily_entries (user_id, adventure_id, date, daily_xp, is_locked)
                VALUES (%s, %s, %s, 0, true)
                RETURNING id;
            """, (TEST_USER_ID, adventure_id, day2))
            entry2_id = cursor.fetchone()[0]

            # Insert 3 more mandatory tasks to deal remaining damage
            for i in range(3):
                cursor.execute("""
                    INSERT INTO tasks (daily_entry_id, content, is_optional, is_completed, category)
                    VALUES (%s, %s, false, true, 'focus');
                """, (entry2_id, f"Day 2 Focus Task {i+1}"))
            db_connection.commit()

            # Process Day 2 round
            cursor.execute("SELECT * FROM calculate_adventure_round(%s, %s);", (adventure_id, day2))
            round2_result = cursor.fetchone()
            damage2, new_hp2 = round2_result
            db_connection.commit()

            # Verify monster is dead (HP = 0)
            assert new_hp2 == 0, f"Monster should be dead (HP=0), got {new_hp2}"

            # Check adventure state before completion
            cursor.execute("""
                SELECT monster_current_hp, total_damage_dealt, current_round, status
                FROM adventures WHERE id = %s;
            """, (adventure_id,))
            hp2, total2, round2_num, status2 = cursor.fetchone()
            assert round2_num == 2
            assert status2 == 'active'
            assert hp2 == 0

            # Step 4: Complete adventure (victory!)
            cursor.execute("SELECT * FROM complete_adventure(%s);", (adventure_id,))
            completion_result = cursor.fetchone()
            final_status, is_victory, xp_earned, already_completed = completion_result
            db_connection.commit()

            # Verify victory
            assert is_victory is True, "Should be a victory"
            assert final_status == 'completed'
            assert xp_earned > 0, f"Should earn XP, got {xp_earned}"
            assert already_completed is False

            # Verify adventure state in DB
            cursor.execute("""
                SELECT status, xp_earned, completed_at, monster_current_hp
                FROM adventures WHERE id = %s;
            """, (adventure_id,))
            adv_status, adv_xp, completed_at, final_hp = cursor.fetchone()
            assert adv_status == 'completed'
            assert adv_xp == xp_earned
            assert completed_at is not None
            assert final_hp == 0

            # Step 5: Verify profile stats updated correctly
            cursor.execute("""
                SELECT adventure_count, monster_defeats, monster_escapes,
                       monster_rating, highest_tier_reached, current_adventure
                FROM profiles WHERE id = %s;
            """, (TEST_USER_ID,))
            adv_count, defeats, escapes, rating, highest, current_adv = cursor.fetchone()

            assert adv_count == 1, "Adventure count should be 1"
            assert defeats == 1, "Monster defeats should be 1"
            assert escapes == 0, "Monster escapes should be 0"
            assert rating == 1, f"Monster rating should increase by 1, got {rating}"
            assert highest == 'easy', "Highest tier should still be easy"
            assert current_adv is None, "Current adventure should be cleared"

        finally:
            cursor.close()

    def test_multi_round_grind_victory_with_categories(self, authenticated_client, cleanup_test_data, db_connection):
        """Full victory cycle: grind down a 200 HP easy monster over 3 rounds with mixed categories.

        Scenario:
        1. Start adventure with 200 HP easy monster
        2. Round 1: Use physical tasks (super-effective vs Sloth = 1.5x) for big damage
        3. Round 2: Mixed categories (some resisted wellness tasks for less damage)
        4. Round 3: Final push with errand tasks (super-effective vs Sloth = 1.5x)
        5. Complete adventure with victory
        6. Verify discoveries were recorded for each category used
        7. Verify profile stats and highest_tier_reached progression
        """
        cursor = db_connection.cursor()
        try:
            # Get a 200 HP easy monster (many easy monsters have 200 HP)
            cursor.execute("""
                SELECT m.id, m.base_hp, m.monster_type
                FROM monsters m
                WHERE m.tier = 'easy' AND m.base_hp >= 200
                LIMIT 1;
            """)
            result = cursor.fetchone()
            if not result:
                pytest.skip("No 200+ HP easy monsters found")
            monster_id, monster_hp, monster_type = result

            # Reset user stats
            cursor.execute("""
                UPDATE profiles SET
                    adventure_count = 0,
                    monster_defeats = 0,
                    monster_escapes = 0,
                    monster_rating = 0,
                    highest_tier_reached = 'easy',
                    current_adventure = NULL
                WHERE id = %s;
            """, (TEST_USER_ID,))
            db_connection.commit()

            # Clear existing discoveries for this user/monster type
            cursor.execute("""
                DELETE FROM type_discoveries
                WHERE user_id = %s AND monster_type = %s;
            """, (TEST_USER_ID, monster_type))
            db_connection.commit()

            # Step 1: Start adventure
            start_response = authenticated_client.post("/api/adventures/start", json={"monster_id": monster_id})
            assert start_response.status_code == 200
            adventure = start_response.json()
            adventure_id = adventure['id']

            assert adventure['monster_current_hp'] == monster_hp

            # Step 2: Round 1 - Physical tasks (SE vs Sloth = 1.5x)
            # 3 mandatory physical tasks vs Sloth = 3 * (100/3 * 1.5) = 150 damage
            day1 = date.today()
            cursor.execute("""
                INSERT INTO daily_entries (user_id, adventure_id, date, daily_xp, is_locked)
                VALUES (%s, %s, %s, 0, true)
                RETURNING id;
            """, (TEST_USER_ID, adventure_id, day1.isoformat()))
            entry1_id = cursor.fetchone()[0]

            for i in range(3):
                cursor.execute("""
                    INSERT INTO tasks (daily_entry_id, content, is_optional, is_completed, category)
                    VALUES (%s, %s, false, true, 'physical');
                """, (entry1_id, f"Round 1 Physical Task {i+1}"))
            db_connection.commit()

            # Process Round 1
            cursor.execute("SELECT * FROM calculate_adventure_round(%s, %s);", (adventure_id, day1.isoformat()))
            damage1, hp_after_r1 = cursor.fetchone()
            db_connection.commit()

            # Physical vs Sloth should deal ~150 damage (capped at 150 or less due to FLOOR)
            assert damage1 >= 149, f"Round 1 with Physical should deal ~150 damage, got {damage1}"
            assert hp_after_r1 < monster_hp, "Monster HP should decrease"

            # Check discoveries recorded for physical
            cursor.execute("""
                SELECT effectiveness FROM type_discoveries
                WHERE user_id = %s AND monster_type = %s AND task_category = 'physical';
            """, (TEST_USER_ID, monster_type))
            phys_effectiveness = cursor.fetchone()
            assert phys_effectiveness is not None, "Physical discovery should be recorded"
            assert phys_effectiveness[0] == 'super_effective', "Physical should be SE vs Sloth"

            # Step 3: Round 2 - Mixed categories (include resisted wellness)
            day2 = day1 + timedelta(days=1)
            cursor.execute("""
                INSERT INTO daily_entries (user_id, adventure_id, date, daily_xp, is_locked)
                VALUES (%s, %s, %s, 0, true)
                RETURNING id;
            """, (TEST_USER_ID, adventure_id, day2.isoformat()))
            entry2_id = cursor.fetchone()[0]

            # 2 focus (neutral) + 1 wellness (resisted 0.5x vs Sloth)
            # Expected: 2*(100/3*1.0) + 1*(100/3*0.5) = ~67 + ~17 = ~84 damage
            cursor.execute("""
                INSERT INTO tasks (daily_entry_id, content, is_optional, is_completed, category)
                VALUES (%s, %s, false, true, 'focus');
            """, (entry2_id, "Round 2 Focus Task 1"))
            cursor.execute("""
                INSERT INTO tasks (daily_entry_id, content, is_optional, is_completed, category)
                VALUES (%s, %s, false, true, 'focus');
            """, (entry2_id, "Round 2 Focus Task 2"))
            cursor.execute("""
                INSERT INTO tasks (daily_entry_id, content, is_optional, is_completed, category)
                VALUES (%s, %s, false, true, 'wellness');
            """, (entry2_id, "Round 2 Wellness Task 1"))
            db_connection.commit()

            # Process Round 2
            cursor.execute("SELECT * FROM calculate_adventure_round(%s, %s);", (adventure_id, day2.isoformat()))
            damage2, hp_after_r2 = cursor.fetchone()
            db_connection.commit()

            # Verify wellness discovery recorded as resisted
            cursor.execute("""
                SELECT effectiveness FROM type_discoveries
                WHERE user_id = %s AND monster_type = %s AND task_category = 'wellness';
            """, (TEST_USER_ID, monster_type))
            well_effectiveness = cursor.fetchone()
            assert well_effectiveness is not None, "Wellness discovery should be recorded"
            assert well_effectiveness[0] == 'resisted', "Wellness should be resisted vs Sloth"

            # Step 4: Round 3 - Finish with errand (SE vs Sloth = 1.5x)
            day3 = day2 + timedelta(days=1)

            # Check if monster is still alive
            cursor.execute("SELECT monster_current_hp FROM adventures WHERE id = %s;", (adventure_id,))
            current_hp = cursor.fetchone()[0]

            if current_hp > 0:
                cursor.execute("""
                    INSERT INTO daily_entries (id, user_id, adventure_id, date, daily_xp, is_locked)
                    VALUES (-- id omitted, let uuid_generate_v4() auto-generate, %s, %s, %s, 0, true)
                    RETURNING id;
                """, (TEST_USER_ID, adventure_id, day3.isoformat()))
                entry3_id = cursor.fetchone()[0]

                # 3 mandatory errand tasks (SE vs Sloth)
                for i in range(3):
                    cursor.execute("""
                        INSERT INTO tasks (daily_entry_id, content, is_optional, is_completed, category)
                        VALUES (%s, %s, false, true, 'errand');
                    """, (entry3_id, f"Round 3 Errand Task {i+1}"))
                db_connection.commit()

                # Process Round 3
                cursor.execute("SELECT * FROM calculate_adventure_round(%s, %s);", (adventure_id, day3.isoformat()))
                damage3, hp_after_r3 = cursor.fetchone()
                db_connection.commit()

                # Verify errand discovery recorded as super-effective
                cursor.execute("""
                    SELECT effectiveness FROM type_discoveries
                    WHERE user_id = %s AND monster_type = %s AND task_category = 'errand';
                """, (TEST_USER_ID, monster_type))
                errand_effectiveness = cursor.fetchone()
                assert errand_effectiveness is not None, "Errand discovery should be recorded"
                assert errand_effectiveness[0] == 'super_effective', "Errand should be SE vs Sloth"

            # Step 5: Complete adventure
            cursor.execute("SELECT * FROM complete_adventure(%s);", (adventure_id,))
            final_status, is_victory, xp_earned, already_completed = cursor.fetchone()
            db_connection.commit()

            assert is_victory is True, "Should be victory"
            assert final_status == 'completed'

            # Step 6: Verify all discoveries recorded
            cursor.execute("""
                SELECT task_category, effectiveness
                FROM type_discoveries
                WHERE user_id = %s AND monster_type = %s
                ORDER BY task_category;
            """, (TEST_USER_ID, monster_type))
            discoveries = cursor.fetchall()

            used_categories = {'physical', 'wellness', 'errand', 'focus'}
            discovered_categories = {cat for cat, eff in discoveries}

            for cat in used_categories:
                assert cat in discovered_categories, f"{cat} discovery should be recorded"

            # Step 7: Verify profile stats
            cursor.execute("""
                SELECT adventure_count, monster_defeats, monster_escapes,
                       monster_rating, highest_tier_reached, total_damage_dealt
                FROM profiles WHERE id = %s;
            """, (TEST_USER_ID,))
            adv_count, defeats, escapes, rating, highest, total_damage = cursor.fetchone()

            assert adv_count == 1, "Adventure count should be 1"
            assert defeats == 1, "Should have 1 defeat"
            assert escapes == 0, "Should have 0 escapes"
            assert rating == 1, f"Rating should be 1, got {rating}"
            assert highest == 'easy', "Highest tier should be easy"
            assert total_damage >= monster_hp, f"Total damage should equal or exceed monster HP"

            # Verify adventure total_damage in DB matches profile
            cursor.execute("SELECT total_damage_dealt FROM adventures WHERE id = %s;", (adventure_id,))
            adv_total_damage = cursor.fetchone()[0]
            assert total_damage >= adv_total_damage, "Profile total_damage should include adventure"

        finally:
            cursor.close()


# =============================================================================
# Test Adventure Edge Cases (E2E)
# =============================================================================

@pytest.mark.e2e
class TestAdventureEdgeCases:
    """Tests for adventure edge cases and boundary conditions."""

    def test_no_tasks_completed_zero_damage(self, authenticated_client, cleanup_test_data, db_connection):
        """When tasks exist but none are completed, should deal 0 damage.

        Scenario:
        1. Start adventure
        2. Create daily entry with tasks (all is_completed = false)
        3. Call calculate_adventure_round
        4. Verify damage = 0, monster HP unchanged
        5. Verify daily_xp = 0
        """
        cursor = db_connection.cursor()
        try:
            # Get a low-HP easy monster
            cursor.execute("SELECT id, base_hp FROM monsters WHERE tier = 'easy' ORDER BY base_hp ASC LIMIT 1;")
            result = cursor.fetchone()
            if not result:
                pytest.skip("No easy monsters found")
            monster_id, monster_hp = result

            # Start adventure
            start_response = authenticated_client.post("/api/adventures/start", json={"monster_id": monster_id})
            assert start_response.status_code == 200
            adventure = start_response.json()
            adventure_id = adventure['id']

            # Create daily entry with tasks but NONE completed
            today = date.today().isoformat()
            cursor.execute("""
                INSERT INTO daily_entries (user_id, adventure_id, date, daily_xp, is_locked)
                VALUES (%s, %s, %s, 0, false)
                RETURNING id;
            """, (TEST_USER_ID, adventure_id, today))
            entry_id = cursor.fetchone()[0]

            # Insert 3 tasks, all incomplete
            for i in range(3):
                cursor.execute("""
                    INSERT INTO tasks (daily_entry_id, content, is_optional, is_completed, category)
                    VALUES (%s, %s, false, false, 'focus');
                """, (entry_id, f"Incomplete Task {i+1}"))
            db_connection.commit()

            # Process round
            cursor.execute("SELECT * FROM calculate_adventure_round(%s, %s);", (adventure_id, today))
            damage, new_hp = cursor.fetchone()
            db_connection.commit()

            # Verify zero damage dealt
            assert damage == 0, f"Expected 0 damage with no completed tasks, got {damage}"
            assert new_hp == monster_hp, f"Monster HP should remain unchanged at {monster_hp}, got {new_hp}"

            # Verify daily_xp stored as 0
            cursor.execute("SELECT daily_xp FROM daily_entries WHERE id = %s;", (entry_id,))
            daily_xp = cursor.fetchone()[0]
            assert daily_xp == 0, f"Daily XP should be 0, got {daily_xp}"

            # Verify adventure stats unchanged
            cursor.execute("""
                SELECT monster_current_hp, total_damage_dealt, current_round
                FROM adventures WHERE id = %s;
            """, (adventure_id,))
            hp, total, round_num = cursor.fetchone()
            assert hp == monster_hp, "Adventure monster HP unchanged"
            assert total == 0, "Total damage should still be 0"
            assert round_num == 1, "Round should have incremented"

        finally:
            cursor.close()

    def test_deadline_passed_auto_complete_as_escaped(self, authenticated_client, cleanup_test_data, db_connection):
        """When deadline passes with monster alive, adventure auto-completes as escaped.

        Scenario:
        1. Start adventure with a 3-day duration
        2. Manually set deadline to yesterday
        3. Monster is still alive (HP > 0)
        4. Complete adventure should mark as 'escaped' with partial XP
        5. Verify profile stats (escapes++, rating--)
        """
        cursor = db_connection.cursor()
        try:
            # Reset user stats
            cursor.execute("""
                UPDATE profiles SET
                    adventure_count = 0,
                    monster_defeats = 0,
                    monster_escapes = 0,
                    monster_rating = 5,
                    highest_tier_reached = 'medium',
                    current_adventure = NULL
                WHERE id = %s;
            """, (TEST_USER_ID,))
            db_connection.commit()

            # Get a 200 HP easy monster
            cursor.execute("SELECT id, base_hp FROM monsters WHERE tier = 'easy' AND base_hp >= 200 LIMIT 1;")
            result = cursor.fetchone()
            if not result:
                pytest.skip("No 200+ HP easy monsters found")
            monster_id, monster_hp = result

            # Start adventure
            start_response = authenticated_client.post("/api/adventures/start", json={"monster_id": monster_id})
            assert start_response.status_code == 200
            adventure = start_response.json()
            adventure_id = adventure['id']

            # Deal some damage but don't kill monster
            today = date.today().isoformat()
            cursor.execute("""
                INSERT INTO daily_entries (user_id, adventure_id, date, daily_xp, is_locked)
                VALUES (%s, %s, %s, 0, true)
                RETURNING id;
            """, (TEST_USER_ID, adventure_id, today))
            entry_id = cursor.fetchone()[0]

            # Insert 2 completed tasks (deals ~67 damage, monster still alive)
            for i in range(2):
                cursor.execute("""
                    INSERT INTO tasks (daily_entry_id, content, is_optional, is_completed, category)
                    VALUES (%s, %s, false, true, 'focus');
                """, (entry_id, f"Partial Task {i+1}"))
            db_connection.commit()

            cursor.execute("SELECT * FROM calculate_adventure_round(%s, %s);", (adventure_id, today))
            damage, new_hp = cursor.fetchone()
            db_connection.commit()

            assert new_hp > 0, "Monster should still be alive after partial damage"

            # Manually set deadline to yesterday (simulate time passed)
            yesterday = (date.today() - timedelta(days=1)).isoformat()
            cursor.execute("UPDATE adventures SET deadline = %s WHERE id = %s;", (yesterday, adventure_id))
            db_connection.commit()

            # Complete adventure (should escape, not victory)
            cursor.execute("SELECT * FROM complete_adventure(%s);", (adventure_id,))
            final_status, is_victory, xp_earned, already_completed = cursor.fetchone()
            db_connection.commit()

            assert is_victory is False, "Should be an escape, not victory"
            assert final_status == 'escaped', f"Status should be 'escaped', got {final_status}"
            assert xp_earned > 0, "Should earn partial XP even on escape"
            assert already_completed is False

            # Verify adventure status in DB
            cursor.execute("SELECT status, xp_earned FROM adventures WHERE id = %s;", (adventure_id,))
            adv_status, adv_xp = cursor.fetchone()
            assert adv_status == 'escaped'
            assert adv_xp == xp_earned

            # Verify profile stats (escape behavior)
            cursor.execute("""
                SELECT adventure_count, monster_defeats, monster_escapes, monster_rating
                FROM profiles WHERE id = %s;
            """, (TEST_USER_ID,))
            adv_count, defeats, escapes, rating = cursor.fetchone()

            assert adv_count == 1, "Adventure count should increment"
            assert defeats == 0, "No defeats on escape"
            assert escapes == 1, "Escapes should increment"
            assert rating == 4, f"Rating should decrease by 1 on escape (5->4), got {rating}"

        finally:
            cursor.close()

    def test_abandon_on_same_day_as_start(self, authenticated_client, cleanup_test_data, db_connection):
        """User abandons adventure on the same day they started it.

        Scenario:
        1. Start adventure
        2. Immediately abandon (no tasks completed, 0 damage dealt)
        3. Verify adventure is marked as escaped with 0 XP
        4. Verify profile stats (escapes++, rating--, current_adventure cleared)
        """
        cursor = db_connection.cursor()
        try:
            # Reset user stats
            cursor.execute("""
                UPDATE profiles SET
                    adventure_count = 0,
                    monster_defeats = 0,
                    monster_escapes = 0,
                    monster_rating = 3,
                    current_adventure = NULL
                WHERE id = %s;
            """, (TEST_USER_ID,))
            db_connection.commit()

            # Get any easy monster
            cursor.execute("SELECT id FROM monsters WHERE tier = 'easy' LIMIT 1;")
            result = cursor.fetchone()
            if not result:
                pytest.skip("No easy monsters found")
            monster_id = result[0]

            # Start adventure
            start_response = authenticated_client.post("/api/adventures/start", json={"monster_id": monster_id})
            assert start_response.status_code == 200
            adventure = start_response.json()
            adventure_id = adventure['id']

            # Immediately abandon (0 damage dealt)
            abandon_response = authenticated_client.post(f"/api/adventures/{adventure_id}/abandon")
            assert abandon_response.status_code == 200
            abandon_data = abandon_response.json()

            # Verify abandon response
            assert 'xp_earned' in abandon_data
            assert abandon_data['xp_earned'] == 0, "Should earn 0 XP when abandoning with 0 damage"

            # Verify adventure status in DB
            cursor.execute("SELECT status, xp_earned, total_damage_dealt FROM adventures WHERE id = %s;", (adventure_id,))
            adv_status, adv_xp, total_damage = cursor.fetchone()

            assert adv_status == 'escaped', f"Status should be 'escaped', got {adv_status}"
            assert adv_xp == 0, "Adventure XP should be 0"
            assert total_damage == 0, "Total damage should be 0"

            # Verify profile current_adventure is cleared
            cursor.execute("SELECT current_adventure FROM profiles WHERE id = %s;", (TEST_USER_ID,))
            current_adv = cursor.fetchone()[0]
            assert current_adv is None, "Current adventure should be None after abandon"

            # Verify profile stats updated correctly
            cursor.execute("""
                SELECT adventure_count, monster_defeats, monster_escapes, monster_rating
                FROM profiles WHERE id = %s;
            """, (TEST_USER_ID,))
            adv_count, defeats, escapes, rating = cursor.fetchone()

            assert adv_count == 1, "Adventure count should increment"
            assert defeats == 0, "No defeats on abandon"
            assert escapes == 1, "Escapes should increment"
            assert rating == 2, f"Rating should decrease by 1 (3->2), got {rating}"

        finally:
            cursor.close()

    def test_tier_unlock_progression(self, authenticated_client, cleanup_test_data, db_connection):
        """Multiple tier unlock progression as rating crosses thresholds.

        Scenario:
        1. Start with rating = 0 (only easy unlocked)
        2. Complete adventure (victory, rating +1)
        3. Start new adventure with higher tier monster
        4. Complete again (rating +1)
        5. Verify highest_tier_reached progression
        6. Verify get_unlocked_tiers returns correct tiers at each rating
        """
        cursor = db_connection.cursor()
        try:
            # Reset to rating = 0 (easy only)
            cursor.execute("""
                UPDATE profiles SET
                    adventure_count = 0,
                    monster_defeats = 0,
                    monster_escapes = 0,
                    monster_rating = 0,
                    highest_tier_reached = 'easy',
                    current_adventure = NULL
                WHERE id = %s;
            """, (TEST_USER_ID,))
            db_connection.commit()

            # Verify unlocked tiers at rating 0
            cursor.execute("SELECT get_unlocked_tiers(%s);", (0,))
            unlocked_0 = cursor.fetchone()[0]
            assert unlocked_0 == ['easy'], f"Rating 0 should unlock ['easy'], got {unlocked_0}"

            # === Victory 1: Easy monster (0 -> 1) ===
            cursor.execute("SELECT id, base_hp FROM monsters WHERE tier = 'easy' ORDER BY base_hp ASC LIMIT 1;")
            result = cursor.fetchone()
            if not result:
                pytest.skip("No easy monsters found")
            easy_monster_id, easy_hp = result

            start_response = authenticated_client.post("/api/adventures/start", json={"monster_id": easy_monster_id})
            assert start_response.status_code == 200
            adventure1 = start_response.json()
            adventure1_id = adventure1['id']

            # Kill monster immediately
            today = date.today().isoformat()
            cursor.execute("""
                INSERT INTO daily_entries (user_id, adventure_id, date, daily_xp, is_locked)
                VALUES (%s, %s, %s, 0, true)
                RETURNING id;
            """, (TEST_USER_ID, adventure1_id, today))
            entry1_id = cursor.fetchone()[0]

            # Insert enough tasks to kill (3 mandatory = ~100 damage for low HP monster)
            for i in range(3):
                cursor.execute("""
                    INSERT INTO tasks (daily_entry_id, content, is_optional, is_completed, category)
                    VALUES (%s, %s, false, true, 'focus');
                """, (entry1_id, f"Kill Task {i+1}"))
            db_connection.commit()

            cursor.execute("SELECT * FROM calculate_adventure_round(%s, %s);", (adventure1_id, today))
            damage1, hp1 = cursor.fetchone()
            db_connection.commit()

            # Force HP to 0 to ensure death
            cursor.execute("UPDATE adventures SET monster_current_hp = 0 WHERE id = %s;", (adventure1_id,))
            db_connection.commit()

            cursor.execute("SELECT * FROM complete_adventure(%s);", (adventure1_id,))
            status1, is_victory1, xp1, _ = cursor.fetchone()
            db_connection.commit()

            assert is_victory1 is True, "First adventure should be victory"

            # Verify rating now = 1, still only easy unlocked
            cursor.execute("SELECT monster_rating, highest_tier_reached FROM profiles WHERE id = %s;", (TEST_USER_ID,))
            rating1, highest1 = cursor.fetchone()
            assert rating1 == 1, f"Rating should be 1 after first victory, got {rating1}"

            cursor.execute("SELECT get_unlocked_tiers(%s);", (rating1,))
            unlocked_1 = cursor.fetchone()[0]
            assert unlocked_1 == ['easy'], f"Rating 1 should still only unlock ['easy'], got {unlocked_1}"

            # === Victory 2-4: Get rating to 5 (unlocks hard) ===
            # Manually increment rating to 5 to test tier unlock
            cursor.execute("UPDATE profiles SET monster_rating = 4 WHERE id = %s;", (TEST_USER_ID,))
            db_connection.commit()

            cursor.execute("SELECT get_unlocked_tiers(%s);", (4,))
            unlocked_4 = cursor.fetchone()[0]
            assert unlocked_4 == ['easy', 'medium'], f"Rating 4 should unlock ['easy', 'medium'], got {unlocked_4}"

            # Increment to 5 (unlocks hard)
            cursor.execute("UPDATE profiles SET monster_rating = 5 WHERE id = %s;", (TEST_USER_ID,))
            db_connection.commit()

            cursor.execute("SELECT get_unlocked_tiers(%s);", (5,))
            unlocked_5 = cursor.fetchone()[0]
            assert unlocked_5 == ['easy', 'medium', 'hard'], f"Rating 5 should unlock ['easy', 'medium', 'hard'], got {unlocked_5}"

            # === Victory at rating 9 (unlocks expert) ===
            cursor.execute("UPDATE profiles SET monster_rating = 9 WHERE id = %s;", (TEST_USER_ID,))
            db_connection.commit()

            cursor.execute("SELECT get_unlocked_tiers(%s);", (9,))
            unlocked_9 = cursor.fetchone()[0]
            assert unlocked_9 == ['easy', 'medium', 'hard', 'expert'], f"Rating 9 should unlock up to 'expert', got {unlocked_9}"

            # === Victory at rating 14 (unlocks boss) ===
            cursor.execute("UPDATE profiles SET monster_rating = 14 WHERE id = %s;", (TEST_USER_ID,))
            db_connection.commit()

            cursor.execute("SELECT get_unlocked_tiers(%s);", (14,))
            unlocked_14 = cursor.fetchone()[0]
            assert unlocked_14 == ['easy', 'medium', 'hard', 'expert', 'boss'], f"Rating 14 should unlock all tiers, got {unlocked_14}"

            # === Victory with hard monster (highest_tier_reached progression) ===
            # Start with hard monster at rating 5
            cursor.execute("UPDATE profiles SET monster_rating = 5, highest_tier_reached = 'medium' WHERE id = %s;", (TEST_USER_ID,))
            db_connection.commit()

            cursor.execute("SELECT id FROM monsters WHERE tier = 'hard' LIMIT 1;")
            result = cursor.fetchone()
            if not result:
                pytest.skip("No hard monsters found")
            hard_monster_id = result[0]

            start_response = authenticated_client.post("/api/adventures/start", json={"monster_id": hard_monster_id})
            assert start_response.status_code == 200
            adventure2 = start_response.json()
            adventure2_id = adventure2['id']

            # Kill and complete
            today2 = date.today().isoformat()
            cursor.execute("""
                INSERT INTO daily_entries (user_id, adventure_id, date, daily_xp, is_locked)
                VALUES (%s, %s, %s, 0, true)
                RETURNING id;
            """, (TEST_USER_ID, adventure2_id, today2))
            entry2_id = cursor.fetchone()[0]

            for i in range(3):
                cursor.execute("""
                    INSERT INTO tasks (daily_entry_id, content, is_optional, is_completed, category)
                    VALUES (%s, %s, false, true, 'focus');
                """, (entry2_id, f"Hard Task {i+1}"))
            db_connection.commit()

            cursor.execute("UPDATE adventures SET monster_current_hp = 0 WHERE id = %s;", (adventure2_id,))
            db_connection.commit()

            cursor.execute("SELECT * FROM complete_adventure(%s);", (adventure2_id,))
            status2, is_victory2, xp2, _ = cursor.fetchone()
            db_connection.commit()

            # Verify highest_tier_reached updated to 'hard'
            cursor.execute("SELECT highest_tier_reached FROM profiles WHERE id = %s;", (TEST_USER_ID,))
            highest2 = cursor.fetchone()[0]
            assert highest2 == 'hard', f"Highest tier should be 'hard' after hard victory, got {highest2}"

        finally:
            cursor.close()


# =============================================================================
# Test Lazy Evaluation (E2E)
# =============================================================================

@pytest.mark.e2e
class TestAdventureLazyEvaluation:
    """Tests for lazy evaluation (catching up on missed rounds)."""

    def test_lazy_evaluation_catches_up_missed_rounds(self, authenticated_client, cleanup_test_data, db_connection):
        """When app wakes from sleep, lazy evaluation should process all missed rounds.

        Scenario:
        1. Start adventure (day 1)
        2. Simulate app sleeping for 2 days (no scheduler runs)
        3. User loads dashboard (triggers GET /api/adventures/current)
        4. Verify lazy evaluation processed all 3 missed rounds
        5. Verify daily_xp is updated for each day
        """
        cursor = db_connection.cursor()
        try:
            # Reset user stats
            cursor.execute("""
                UPDATE profiles SET
                    adventure_count = 0,
                    monster_defeats = 0,
                    monster_escapes = 0,
                    monster_rating = 0,
                    current_adventure = NULL
                WHERE id = %s;
            """, (TEST_USER_ID,))
            db_connection.commit()

            # Get a low-HP easy monster (will die in 2 rounds)
            cursor.execute("SELECT id, base_hp FROM monsters WHERE tier = 'easy' ORDER BY base_hp ASC LIMIT 1;")
            result = cursor.fetchone()
            if not result:
                pytest.skip("No easy monsters found")
            monster_id, monster_hp = result

            # Step 1: Start adventure 2 days ago (simulate missed rounds)
            start_date = date.today() - timedelta(days=3)
            deadline = start_date + timedelta(days=5)

            cursor.execute("""
                INSERT INTO adventures (id, user_id, monster_id, start_date, deadline,
                    monster_max_hp, monster_current_hp, duration, status, current_round)
                VALUES (gen_random_uuid(), %s, %s, %s, %s, %s, %s, 5, 'active', 0)
                RETURNING id;
            """, (TEST_USER_ID, monster_id, start_date.isoformat(), deadline.isoformat(),
                      monster_hp, monster_hp))
            adventure_id = cursor.fetchone()[0]
            db_connection.commit()

            # Step 2: Simulate app sleeping - create daily entries for past 3 days with completed tasks
            # Day 1 (2 days ago)
            day1 = start_date.isoformat()
            cursor.execute("""
                INSERT INTO daily_entries (user_id, adventure_id, date, daily_xp, is_locked)
                VALUES (%s, %s, %s, 0, true)
                RETURNING id;
            """, (TEST_USER_ID, adventure_id, day1))
            entry1_id = cursor.fetchone()[0]

            for i in range(3):
                cursor.execute("""
                    INSERT INTO tasks (daily_entry_id, content, is_optional, is_completed, category)
                    VALUES (%s, %s, false, true, 'focus');
                """, (entry1_id, f"Day 1 Task {i+1}"))

            # Day 2 (1 day ago)
            day2 = (start_date + timedelta(days=1)).isoformat()
            cursor.execute("""
                INSERT INTO daily_entries (user_id, adventure_id, date, daily_xp, is_locked)
                VALUES (%s, %s, %s, 0, true)
                RETURNING id;
            """, (TEST_USER_ID, adventure_id, day2))
            entry2_id = cursor.fetchone()[0]

            for i in range(3):
                cursor.execute("""
                    INSERT INTO tasks (daily_entry_id, content, is_optional, is_completed, category)
                    VALUES (%s, %s, false, true, 'focus');
                """, (entry2_id, f"Day 2 Task {i+1}"))

            # Day 3 (today)
            day3 = (start_date + timedelta(days=2)).isoformat()
            cursor.execute("""
                INSERT INTO daily_entries (user_id, adventure_id, date, daily_xp, is_locked)
                VALUES (%s, %s, %s, 0, true)
                RETURNING id;
            """, (TEST_USER_ID, adventure_id, day3))
            entry3_id = cursor.fetchone()[0]

            for i in range(3):
                cursor.execute("""
                    INSERT INTO tasks (daily_entry_id, content, is_optional, is_completed, category)
                    VALUES (%s, %s, false, true, 'focus');
                """, (entry3_id, f"Day 3 Task {i+1}"))
            db_connection.commit()

            # Verify current_round is still 0 (no processing yet)
            cursor.execute("SELECT current_round FROM adventures WHERE id = %s;", (adventure_id,))
            current_round_before = cursor.fetchone()[0]
            assert current_round_before == 0, f"current_round should be 0 before lazy eval, got {current_round_before}"

            # Verify daily_xp is 0 for all entries
            cursor.execute("""
                SELECT date, daily_xp FROM daily_entries
                WHERE adventure_id = %s ORDER BY date;
            """, (adventure_id,))
            entries_before = cursor.fetchall()
            for entry_date, daily_xp in entries_before:
                assert daily_xp == 0, f"daily_xp should be 0 before lazy eval for {entry_date}, got {daily_xp}"

            # Step 3: Trigger lazy evaluation by calling GET /api/adventures/current
            current_response = authenticated_client.get("/api/adventures/current")
            assert current_response.status_code == 200
            adventure_data = current_response.json()

            # Step 4: Verify lazy evaluation processed all 3 rounds
            cursor.execute("SELECT current_round, monster_current_hp, total_damage_dealt FROM adventures WHERE id = %s;", (adventure_id,))
            current_round_after, hp_after, total_damage = cursor.fetchone()

            # Should have processed 3 rounds (killed monster)
            assert current_round_after == 3, f"current_round should be 3 after lazy eval, got {current_round_after}"
            assert hp_after == 0, f"Monster should be dead (HP=0) after 3 rounds, got {hp_after}"
            assert total_damage > 0, f"Total damage should be > 0, got {total_damage}"

            # Verify daily_xp is now updated for all 3 entries
            cursor.execute("""
                SELECT date, daily_xp FROM daily_entries
                WHERE adventure_id = %s ORDER BY date;
            """, (adventure_id,))
            entries_after = cursor.fetchall()

            total_xp = 0
            for entry_date, daily_xp in entries_after:
                assert daily_xp > 0, f"daily_xp should be > 0 after lazy eval for {entry_date}, got {daily_xp}"
                total_xp += daily_xp

            # Total XP across all days should match total_damage_dealt
            assert total_xp == total_damage, f"Sum of daily_xp ({total_xp}) should equal total_damage_dealt ({total_damage})"

        finally:
            cursor.close()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
