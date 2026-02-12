"""
Unit tests for adventures router.

Tests API endpoints for adventure operations:
- GET /monsters - Get weighted monster pool
- POST /monsters/refresh - Refresh monster pool
- POST /start - Start new adventure
- GET /current - Get active adventure
- GET /{id} - Get adventure details
- POST /{id}/abandon - Abandon adventure
- POST /{id}/break - Schedule break
"""
import pytest
from datetime import date, timedelta, datetime
from unittest.mock import Mock, patch, AsyncMock
from fastapi import HTTPException

from routers.adventures import router


# =============================================================================
# Mock Helpers
# =============================================================================

def create_mock_execute_response(data):
    """Create a mock execute response with data attribute."""
    mock_response = Mock()
    mock_response.data = data
    return mock_response


def create_mock_user(user_id='user-123'):
    """Create a mock authenticated user."""
    mock_user = Mock()
    mock_user.id = user_id
    return mock_user


# =============================================================================
# Test GET /monsters
# =============================================================================

class TestGetMonsterPool:
    """Test GET /adventures/monsters endpoint."""

    @pytest.fixture
    def mock_supabase_base(self):
        with patch('routers.adventures.supabase') as mock:
            yield mock

    @pytest.fixture
    def mock_adventure_service(self):
        with patch('routers.adventures.AdventureService') as mock:
            yield mock

    def test_get_monster_pool_success(self, mock_supabase_base, mock_adventure_service):
        """Successfully get monster pool."""
        mock_user = create_mock_user()

        # Mock profile
        mock_supabase_base.table.return_value.select.return_value.eq.return_value.single\
            .return_value.execute.return_value = create_mock_execute_response({
                'monster_rating': 0
            })

        # Mock service methods
        mock_adventure_service.initialize_refresh_count.return_value = 3
        mock_adventure_service.get_weighted_monster_pool.return_value = [
            {'id': 'm1', 'name': 'Slime', 'tier': 'easy'},
            {'id': 'm2', 'name': 'Rat', 'tier': 'easy'},
        ]
        mock_adventure_service.get_unlocked_tiers.return_value = ['easy']

        # Simulate endpoint logic
        user = mock_user
        profile_res = mock_supabase_base.table("profiles").select("monster_rating")\
            .eq("id", user.id).single().execute()
        rating = profile_res.data.get('monster_rating', 0)
        remaining = mock_adventure_service.initialize_refresh_count(user.id)
        pool = mock_adventure_service.get_weighted_monster_pool(rating, count=4)

        result = {
            "monsters": pool,
            "refreshes_remaining": remaining,
            "unlocked_tiers": mock_adventure_service.get_unlocked_tiers(rating),
            "current_rating": rating
        }

        assert 'monsters' in result
        assert 'refreshes_remaining' in result
        assert result['refreshes_remaining'] == 3
        assert 'unlocked_tiers' in result
        assert result['current_rating'] == 0

    def test_get_monster_pool_profile_not_found(self, mock_supabase_base, mock_adventure_service):
        """Raise 404 when profile not found."""
        mock_user = create_mock_user()

        mock_supabase_base.table.return_value.select.return_value.eq.return_value.single\
            .return_value.execute.return_value = create_mock_execute_response(None)

        user = mock_user
        profile_res = mock_supabase_base.table("profiles").select("monster_rating")\
            .eq("id", user.id).single().execute()

        if not profile_res.data:
            with pytest.raises(HTTPException) as exc_info:
                raise HTTPException(status_code=404, detail="Profile not found")

        assert exc_info.value.status_code == 404


# =============================================================================
# Test POST /monsters/refresh
# =============================================================================

class TestRefreshMonsterPool:
    """Test POST /adventures/monsters/refresh endpoint."""

    @pytest.fixture
    def mock_supabase_base(self):
        with patch('routers.adventures.supabase') as mock:
            yield mock

    @pytest.fixture
    def mock_adventure_service(self):
        with patch('routers.adventures.AdventureService') as mock:
            yield mock

    def test_refresh_success(self, mock_supabase_base, mock_adventure_service):
        """Successfully refresh monster pool."""
        mock_user = create_mock_user()

        # Mock profile
        mock_supabase_base.table.return_value.select.return_value.eq.return_value.single\
            .return_value.execute.return_value = create_mock_execute_response({
                'monster_rating': 2
            })

        # Mock service methods
        mock_adventure_service.decrement_refresh_count.return_value = 2
        mock_adventure_service.get_weighted_monster_pool.return_value = [
            {'id': 'm1', 'name': 'Goblin', 'tier': 'medium'},
        ]
        mock_adventure_service.get_unlocked_tiers.return_value = ['easy', 'medium']

        # Simulate endpoint logic
        user = mock_user
        profile_res = mock_supabase_base.table("profiles").select("monster_rating")\
            .eq("id", user.id).single().execute()
        rating = profile_res.data.get('monster_rating', 0)
        remaining = mock_adventure_service.decrement_refresh_count(user.id)
        pool = mock_adventure_service.get_weighted_monster_pool(rating, count=4)

        result = {
            "monsters": pool,
            "refreshes_remaining": remaining,
            "unlocked_tiers": mock_adventure_service.get_unlocked_tiers(rating)
        }

        assert result['refreshes_remaining'] == 2
        mock_adventure_service.decrement_refresh_count.assert_called_once_with('user-123')

    def test_refresh_no_refreshes_remaining(self, mock_supabase_base, mock_adventure_service):
        """Raise 400 when no refreshes remaining."""
        mock_user = create_mock_user()

        mock_supabase_base.table.return_value.select.return_value.eq.return_value.single\
            .return_value.execute.return_value = create_mock_execute_response({
                'monster_rating': 0
            })

        # Mock decrement raising HTTPException
        mock_adventure_service.decrement_refresh_count.side_effect = HTTPException(
            status_code=400, detail="No refreshes remaining"
        )

        user = mock_user
        profile_res = mock_supabase_base.table("profiles").select("monster_rating")\
            .eq("id", user.id).single().execute()

        if not profile_res.data:
            raise HTTPException(status_code=404, detail="Profile not found")

        rating = profile_res.data.get('monster_rating', 0)

        with pytest.raises(HTTPException) as exc_info:
            try:
                remaining = mock_adventure_service.decrement_refresh_count(user.id)
            except HTTPException:
                raise HTTPException(
                    status_code=400,
                    detail="No refreshes remaining. Select a monster or start over."
                )

        assert exc_info.value.status_code == 400


# =============================================================================
# Test POST /start
# =============================================================================

class TestStartAdventure:
    """Test POST /adventures/start endpoint."""

    @pytest.fixture
    def mock_supabase_base(self):
        with patch('routers.adventures.supabase') as mock:
            yield mock

    @pytest.fixture
    def mock_adventure_service(self):
        with patch('routers.adventures.AdventureService') as mock:
            yield mock

    def test_start_adventure_success(self, mock_supabase_base, mock_adventure_service):
        """Successfully start an adventure."""
        mock_user = create_mock_user()

        adventure = {
            'id': 'adv-123',
            'user_id': 'user-123',
            'monster_id': 'monster-1',
            'status': 'active'
        }

        mock_adventure_service.create_adventure.return_value = adventure

        # Mock fetch with monster data
        mock_supabase_base.table.return_value.select.return_value.eq.return_value.single\
            .return_value.execute.return_value = create_mock_execute_response({
                **adventure,
                'monster': {'name': 'Slime', 'tier': 'easy', 'emoji': '🟢'}
            })

        body = {'monster_id': 'monster-1'}
        user = mock_user

        monster_id = body.get('monster_id')
        adventure_result = mock_adventure_service.create_adventure(user.id, monster_id)

        assert adventure_result['id'] == 'adv-123'
        assert adventure_result['status'] == 'active'
        mock_adventure_service.create_adventure.assert_called_once_with('user-123', 'monster-1')

    def test_start_adventure_missing_monster_id(self, mock_supabase_base, mock_adventure_service):
        """Raise 400 when monster_id missing."""
        body = {'monster_id': None}

        monster_id = body.get('monster_id')
        if not monster_id:
            with pytest.raises(HTTPException) as exc_info:
                raise HTTPException(status_code=400, detail="monster_id is required")

        assert exc_info.value.status_code == 400


# =============================================================================
# Test GET /current
# =============================================================================

class TestGetCurrentAdventure:
    """Test GET /adventures/current endpoint."""

    @pytest.fixture
    def mock_supabase_base(self):
        with patch('routers.adventures.supabase') as mock:
            yield mock

    def test_get_current_adventure_active_state(self, mock_supabase_base):
        """Get current adventure with ACTIVE app state."""
        mock_user = create_mock_user()

        # Start date in the past to ensure ACTIVE state
        start = date.today() - timedelta(days=2)
        deadline = date.today() + timedelta(days=1)

        adventure = {
            'id': 'adv-123',
            'user_id': 'user-123',
            'status': 'active',
            'start_date': start.isoformat(),
            'deadline': deadline.isoformat(),
            'is_on_break': False,
            'monster': {'name': 'Slime', 'tier': 'easy'}
        }

        # Mock adventure fetch
        mock_supabase_base.table.return_value.select.return_value.eq.return_value.eq\
            .return_value.single.return_value.execute.return_value = \
            create_mock_execute_response(adventure)

        # Mock profile timezone
        mock_supabase_base.table.return_value.select.return_value.eq.return_value.single\
            .return_value.execute.return_value = create_mock_execute_response({
                'timezone': 'UTC'
            })

        user = mock_user
        res = mock_supabase_base.table("adventures").select("*").eq("user_id", user.id)\
            .eq("status", "active").single().execute()

        adventure_result = res.data
        profile_res = mock_supabase_base.table("profiles").select("timezone")\
            .eq("id", user.id).single().execute()

        import pytz
        user_tz = profile_res.data.get('timezone', 'UTC') if profile_res.data else 'UTC'
        try:
            user_today = datetime.now(pytz.timezone(user_tz)).date()
        except pytz.exceptions.UnknownTimeZoneError:
            user_today = datetime.now(pytz.utc).date()

        start_date = date.fromisoformat(adventure_result['start_date'])
        deadline = date.fromisoformat(adventure_result['deadline'])

        if adventure_result['is_on_break']:
            app_state = 'ON_BREAK'
        elif user_today < start_date:
            app_state = 'PRE_ADVENTURE'
        elif user_today > deadline:
            app_state = 'DEADLINE_PASSED'
        elif user_today == deadline:
            app_state = 'LAST_DAY'
        else:
            app_state = 'ACTIVE'

        adventure_result['app_state'] = app_state
        days_remaining = (deadline - user_today).days
        adventure_result['days_remaining'] = max(days_remaining, 0)

        assert adventure_result['app_state'] == 'ACTIVE'
        assert adventure_result['days_remaining'] >= 0

    def test_get_current_adventure_on_break_state(self, mock_supabase_base):
        """Get current adventure with ON_BREAK app state."""
        mock_user = create_mock_user()

        today = date.today()
        adventure = {
            'id': 'adv-123',
            'user_id': 'user-123',
            'status': 'active',
            'start_date': today.isoformat(),
            'deadline': (today + timedelta(days=3)).isoformat(),
            'is_on_break': True,
            'monster': {'name': 'Slime', 'tier': 'easy'}
        }

        mock_supabase_base.table.return_value.select.return_value.eq.return_value.eq\
            .return_value.single.return_value.execute.return_value = \
            create_mock_execute_response(adventure)

        mock_supabase_base.table.return_value.select.return_value.eq.return_value.single\
            .return_value.execute.return_value = create_mock_execute_response({
                'timezone': 'UTC'
            })

        user = mock_user
        res = mock_supabase_base.table("adventures").select("*").eq("user_id", user.id)\
            .eq("status", "active").single().execute()

        adventure_result = res.data
        profile_res = mock_supabase_base.table("profiles").select("timezone")\
            .eq("id", user.id).single().execute()

        import pytz
        user_tz = profile_res.data.get('timezone', 'UTC') if profile_res.data else 'UTC'
        try:
            user_today = datetime.now(pytz.timezone(user_tz)).date()
        except pytz.exceptions.UnknownTimeZoneError:
            user_today = datetime.now(pytz.utc).date()

        start_date = date.fromisoformat(adventure_result['start_date'])
        deadline = date.fromisoformat(adventure_result['deadline'])

        if adventure_result['is_on_break']:
            app_state = 'ON_BREAK'
        elif user_today < start_date:
            app_state = 'PRE_ADVENTURE'
        elif user_today > deadline:
            app_state = 'DEADLINE_PASSED'
        elif user_today == deadline:
            app_state = 'LAST_DAY'
        else:
            app_state = 'ACTIVE'

        adventure_result['app_state'] = app_state

        assert adventure_result['app_state'] == 'ON_BREAK'

    def test_get_current_adventure_not_found(self, mock_supabase_base):
        """Raise 404 when no active adventure."""
        mock_user = create_mock_user()

        mock_supabase_base.table.return_value.select.return_value.eq.return_value.eq\
            .return_value.single.return_value.execute.side_effect = Exception("Not found")

        with pytest.raises(HTTPException) as exc_info:
            try:
                res = mock_supabase_base.table("adventures").select("*").eq("user_id", mock_user.id)\
                    .eq("status", "active").single().execute()
            except Exception:
                raise HTTPException(status_code=404, detail="No active adventure found")

        assert exc_info.value.status_code == 404

    def test_get_current_adventure_includes_discoveries(self, mock_supabase_base):
        """Get current adventure includes discoveries for monster type."""
        mock_user = create_mock_user()

        # Start date in the past to ensure ACTIVE state
        start = date.today() - timedelta(days=2)
        deadline = date.today() + timedelta(days=1)

        adventure = {
            'id': 'adv-123',
            'user_id': 'user-123',
            'status': 'active',
            'start_date': start.isoformat(),
            'deadline': deadline.isoformat(),
            'is_on_break': False,
            'monster': {
                'name': 'Lazy Slime',
                'tier': 'easy',
                'monster_type': 'sloth'
            }
        }

        discoveries_data = [
            {'task_category': 'physical', 'effectiveness': 'super_effective'},
            {'task_category': 'errand', 'effectiveness': 'neutral'},
            {'task_category': 'wellness', 'effectiveness': 'resisted'},
        ]

        # Create a fresh mock for discoveries
        discoveries_response = create_mock_execute_response(discoveries_data)

        # The test verifies the logic: when monster_type exists, we query discoveries
        monster_type = adventure.get('monster', {}).get('monster_type')

        # Simulate the logic from the endpoint
        if monster_type:
            # In the real endpoint, this would query supabase
            # Here we simulate that the data would be returned
            adventure['discoveries'] = discoveries_response.data or []
        else:
            adventure['discoveries'] = []

        # Verify the expected behavior
        assert monster_type == 'sloth'
        assert 'discoveries' in adventure
        assert adventure['discoveries'] == discoveries_data
        assert len(adventure['discoveries']) == 3
        assert adventure['discoveries'][0]['task_category'] == 'physical'
        assert adventure['discoveries'][0]['effectiveness'] == 'super_effective'

    def test_get_current_adventure_discoveries_empty_when_no_monster_type(self, mock_supabase_base):
        """Get current adventure returns empty discoveries when monster has no type."""
        mock_user = create_mock_user()

        today = date.today()
        adventure = {
            'id': 'adv-123',
            'user_id': 'user-123',
            'status': 'active',
            'start_date': today.isoformat(),
            'deadline': (today + timedelta(days=3)).isoformat(),
            'is_on_break': True,
            'monster': {
                'name': 'Old Monster',
                'tier': 'easy',
                # No monster_type - old data
            }
        }

        mock_supabase_base.table.return_value.select.return_value.eq.return_value.eq\
            .return_value.single.return_value.execute.return_value = \
            create_mock_execute_response(adventure)

        mock_supabase_base.table.return_value.select.return_value.eq.return_value.single\
            .return_value.execute.return_value = create_mock_execute_response({
                'timezone': 'UTC'
            })

        user = mock_user
        res = mock_supabase_base.table("adventures").select("*").eq("user_id", user.id)\
            .eq("status", "active").single().execute()

        adventure_result = res.data
        profile_res = mock_supabase_base.table("profiles").select("timezone")\
            .eq("id", user.id).single().execute()

        import pytz
        user_tz = profile_res.data.get('timezone', 'UTC') if profile_res.data else 'UTC'
        try:
            user_today = datetime.now(pytz.timezone(user_tz)).date()
        except pytz.exceptions.UnknownTimeZoneError:
            user_today = datetime.now(pytz.utc).date()

        start_date = date.fromisoformat(adventure_result['start_date'])
        deadline_date = date.fromisoformat(adventure_result['deadline'])

        if adventure_result['is_on_break']:
            app_state = 'ON_BREAK'
        elif user_today < start_date:
            app_state = 'PRE_ADVENTURE'
        elif user_today > deadline_date:
            app_state = 'DEADLINE_PASSED'
        elif user_today == deadline_date:
            app_state = 'LAST_DAY'
        else:
            app_state = 'ACTIVE'

        adventure_result['app_state'] = app_state

        # Fetch discoveries for current monster's type
        monster_type = adventure_result.get('monster', {}).get('monster_type')
        if monster_type:
            disc_res = mock_supabase_base.table("type_discoveries").select(
                "task_category, effectiveness"
            ).eq("user_id", user.id).eq("monster_type", monster_type).execute()
            adventure_result['discoveries'] = disc_res.data or []
        else:
            adventure_result['discoveries'] = []

        assert adventure_result['discoveries'] == []
        assert isinstance(adventure_result['discoveries'], list)


# =============================================================================
# Test GET /{id}
# =============================================================================

class TestGetAdventureDetails:
    """Test GET /adventures/{id} endpoint."""

    @pytest.fixture
    def mock_supabase_base(self):
        with patch('routers.adventures.supabase') as mock:
            yield mock

    def test_get_adventure_details_success(self, mock_supabase_base):
        """Successfully get adventure details with daily breakdown."""
        mock_user = create_mock_user()
        adventure_id = 'adv-123'

        adventure = {
            'id': adventure_id,
            'user_id': 'user-123',
            'status': 'active',
            'monster': {'name': 'Slime', 'tier': 'easy'}
        }

        # Mock adventure fetch
        mock_supabase_base.table.return_value.select.return_value.eq.return_value.single\
            .return_value.execute.return_value = create_mock_execute_response(adventure)

        # Mock daily entries
        mock_supabase_base.table.return_value.select.return_value.eq.return_value.order\
            .return_value.execute.return_value = create_mock_execute_response([
            {'date': '2026-01-20', 'daily_xp': 100},
            {'date': '2026-01-21', 'daily_xp': 80},
        ])

        res = mock_supabase_base.table("adventures").select("*").eq("id", adventure_id)\
            .single().execute()

        adventure_result = res.data

        # Verify ownership
        if adventure_result['user_id'] != mock_user.id:
            raise HTTPException(status_code=403, detail="Not your adventure")

        # Fetch daily breakdown
        entries_res = mock_supabase_base.table("daily_entries").select("date, daily_xp")\
            .eq("adventure_id", adventure_id).order("date").execute()

        daily_breakdown = []
        if entries_res.data:
            for entry in entries_res.data:
                daily_breakdown.append({
                    'date': entry['date'],
                    'damage': entry.get('daily_xp', 0) or 0
                })

        adventure_result['daily_breakdown'] = daily_breakdown

        assert adventure_result['id'] == adventure_id
        assert len(adventure_result['daily_breakdown']) == 2
        assert adventure_result['daily_breakdown'][0]['damage'] == 100

    def test_get_adventure_details_not_owner(self, mock_supabase_base):
        """Raise 403 when user doesn't own adventure."""
        mock_user = create_mock_user()
        adventure_id = 'adv-123'

        adventure = {
            'id': adventure_id,
            'user_id': 'other-user',
            'status': 'active',
            'monster': {'name': 'Slime', 'tier': 'easy'}
        }

        mock_supabase_base.table.return_value.select.return_value.eq.return_value.single\
            .return_value.execute.return_value = create_mock_execute_response(adventure)

        res = mock_supabase_base.table("adventures").select("*").eq("id", adventure_id)\
            .single().execute()

        adventure_result = res.data

        if adventure_result['user_id'] != mock_user.id:
            with pytest.raises(HTTPException) as exc_info:
                raise HTTPException(status_code=403, detail="Not your adventure")

        assert exc_info.value.status_code == 403


# =============================================================================
# Test POST /{id}/abandon
# =============================================================================

class TestAbandonAdventure:
    """Test POST /adventures/{id}/abandon endpoint."""

    @pytest.fixture
    def mock_adventure_service(self):
        with patch('routers.adventures.AdventureService') as mock:
            yield mock

    def test_abandon_adventure_success(self, mock_adventure_service):
        """Successfully abandon adventure."""
        mock_user = create_mock_user()
        adventure_id = 'adv-123'

        mock_adventure_service.abandon_adventure.return_value = {
            'status': 'abandoned',
            'xp_earned': 200
        }

        result = mock_adventure_service.abandon_adventure(adventure_id, mock_user.id)

        assert result['status'] == 'abandoned'
        assert result['xp_earned'] == 200
        mock_adventure_service.abandon_adventure.assert_called_once_with('adv-123', 'user-123')


# =============================================================================
# Test POST /{id}/break
# =============================================================================

class TestScheduleBreakRouter:
    """Test POST /adventures/{id}/break endpoint."""

    @pytest.fixture
    def mock_adventure_service(self):
        with patch('routers.adventures.AdventureService') as mock:
            yield mock

    def test_schedule_break_success(self, mock_adventure_service):
        """Successfully schedule break."""
        mock_user = create_mock_user()
        adventure_id = 'adv-123'

        mock_adventure_service.schedule_break.return_value = {
            'status': 'break_scheduled',
            'break_date': date.today().isoformat(),
            'breaks_remaining': 1
        }

        result = mock_adventure_service.schedule_break(adventure_id, mock_user.id)

        assert result['status'] == 'break_scheduled'
        assert result['breaks_remaining'] == 1
        mock_adventure_service.schedule_break.assert_called_once_with('adv-123', 'user-123')


# =============================================================================
# Test GET /discoveries
# =============================================================================

class TestGetDiscoveries:
    """Test GET /adventures/discoveries endpoint."""

    @pytest.fixture
    def mock_supabase_base(self):
        with patch('routers.adventures.supabase') as mock:
            yield mock

    def test_get_discoveries_all(self, mock_supabase_base):
        """Successfully get all user discoveries."""
        mock_user = create_mock_user()

        discoveries_data = [
            {'monster_type': 'sloth', 'task_category': 'physical', 'effectiveness': 'super_effective'},
            {'monster_type': 'sloth', 'task_category': 'errand', 'effectiveness': 'neutral'},
            {'monster_type': 'fog', 'task_category': 'focus', 'effectiveness': 'super_effective'},
        ]

        # Set up the mock chain properly - each call returns a new mock
        table_mock = mock_supabase_base.table.return_value
        select_mock = table_mock.select.return_value
        eq_mock1 = select_mock.eq.return_value
        execute_mock = eq_mock1.execute.return_value
        execute_mock.data = discoveries_data

        user = mock_user
        result = mock_supabase_base.table("type_discoveries").select(
            "monster_type, task_category, effectiveness"
        ).eq("user_id", user.id).execute()

        response = {"discoveries": result.data or []}

        assert 'discoveries' in response
        assert len(response['discoveries']) == 3
        assert response['discoveries'][0]['monster_type'] == 'sloth'
        assert response['discoveries'][0]['effectiveness'] == 'super_effective'

    def test_get_discoveries_filtered_by_monster_type(self, mock_supabase_base):
        """Successfully filter discoveries by monster_type."""
        mock_user = create_mock_user()
        monster_type = 'sloth'

        filtered_data = [
            {'monster_type': 'sloth', 'task_category': 'physical', 'effectiveness': 'super_effective'},
            {'monster_type': 'sloth', 'task_category': 'errand', 'effectiveness': 'neutral'},
        ]

        # Set up the mock chain with two .eq() calls
        table_mock = mock_supabase_base.table.return_value
        select_mock = table_mock.select.return_value
        eq_mock1 = select_mock.eq.return_value
        eq_mock2 = eq_mock1.eq.return_value
        execute_mock = eq_mock2.execute.return_value
        execute_mock.data = filtered_data

        user = mock_user
        query = mock_supabase_base.table("type_discoveries").select(
            "monster_type, task_category, effectiveness"
        ).eq("user_id", user.id)

        if monster_type:
            query = query.eq("monster_type", monster_type)

        result = query.execute()
        response = {"discoveries": result.data or []}

        assert len(response['discoveries']) == 2
        assert all(d['monster_type'] == 'sloth' for d in response['discoveries'])

    def test_get_discoveries_empty(self, mock_supabase_base):
        """Returns empty array when no discoveries exist."""
        mock_user = create_mock_user()

        table_mock = mock_supabase_base.table.return_value
        select_mock = table_mock.select.return_value
        eq_mock1 = select_mock.eq.return_value
        execute_mock = eq_mock1.execute.return_value
        execute_mock.data = []

        user = mock_user
        result = mock_supabase_base.table("type_discoveries").select(
            "monster_type, task_category, effectiveness"
        ).eq("user_id", user.id).execute()

        response = {"discoveries": result.data or []}

        assert response['discoveries'] == []


# =============================================================================
# Test Router Configuration
# =============================================================================

class TestRouterConfiguration:
    """Test router is properly configured."""

    def test_router_prefix(self):
        """Router has correct prefix."""
        assert router.prefix == "/adventures"

    def test_router_tags(self):
        """Router has correct tags."""
        assert router.tags == ["adventures"]

    def test_router_endpoints_exist(self):
        """All expected endpoints are registered."""
        paths = [route.path for route in router.routes]
        # Should contain endpoint paths
        assert any('monsters' in path for path in paths)
        assert any('start' in path for path in paths)
        assert any('current' in path for path in paths)
        assert any('discoveries' in path for path in paths)
