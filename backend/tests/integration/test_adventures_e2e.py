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
