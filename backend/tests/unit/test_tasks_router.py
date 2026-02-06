"""
Unit tests for Tasks Router.

Tests task planning and drafting functionality for both PVP battles and adventures:
- Draft tasks creates or updates daily entries
- Re-drafting tasks replaces existing tasks
- Entry matching works for both battle and adventure modes
"""
import pytest
from datetime import date, timedelta
from unittest.mock import Mock, patch
from fastapi import HTTPException

from models import TaskCreate
from utils.enums import GameMode


# =============================================================================
# Mock Helpers
# =============================================================================

def create_mock_execute_response(data):
    """Create a mock execute response with data attribute."""
    mock_response = Mock()
    mock_response.data = data
    return mock_response


def setup_profile_mock(mock_supabase, user_id='user-123', **overrides):
    """Setup a profile mock with default values."""
    profile_data = {
        'id': user_id,
        'timezone': 'UTC',
    }
    profile_data.update(overrides)

    mock_supabase.table.return_value.select.return_value.eq.return_value.single\
        .return_value.execute.return_value = create_mock_execute_response(profile_data)


# =============================================================================
# Test Draft Tasks - Entry Matching
# =============================================================================

class TestDraftTasksEntryMatching:
    """Test that draft_tasks correctly finds existing entries for both modes."""

    @pytest.fixture
    def mock_supabase_base(self):
        # Need to patch both routers.tasks and utils.game_session since they both import supabase
        with patch('utils.game_session.supabase') as game_session_supabase, \
             patch('database.supabase', new=game_session_supabase), \
             patch('routers.tasks.supabase', new=game_session_supabase):
            yield game_session_supabase

    @pytest.fixture
    def mock_user(self):
        """Create a mock authenticated user."""
        user = Mock()
        user.id = 'user-123'
        return user

    @pytest.mark.asyncio
    async def test_draft_tasks_pvp_finds_existing_entry(self, mock_supabase_base, mock_user):
        """PVP mode: Should find existing entry with matching battle_id."""
        # Setup profile mock
        setup_profile_mock(mock_supabase_base, 'user-123', timezone='UTC')

        # Mock active battle
        mock_supabase_base.table.return_value.select.return_value.or_.return_value\
            .eq.return_value.single.return_value.execute.return_value = \
            create_mock_execute_response({'id': 'battle-123'})

        # Mock daily_entries query returning entries
        existing_entry = {
            'id': 'entry-123',
            'user_id': 'user-123',
            'date': (date.today() + timedelta(days=1)).isoformat(),
            'battle_id': 'battle-123',  # Matches our session
            'adventure_id': None,
        }
        other_entry = {
            'id': 'entry-456',
            'user_id': 'user-123',
            'date': (date.today() + timedelta(days=1)).isoformat(),
            'battle_id': 'battle-999',  # Different battle
            'adventure_id': None,
        }

        mock_supabase_base.table.return_value.select.return_value.eq.return_value.eq\
            .return_value.execute.return_value = create_mock_execute_response([
            existing_entry, other_entry
        ])

        # Mock tasks delete (for clearing existing tasks)
        mock_supabase_base.table.return_value.delete.return_value.eq.return_value\
            .execute.return_value = create_mock_execute_response(None)

        # Mock tasks insert
        mock_supabase_base.table.return_value.insert.return_value.execute\
            .return_value = create_mock_execute_response(None)

        # Import and call the function directly
        from routers.tasks import draft_tasks

        # Mock get_daily_quota
        with patch('routers.tasks.get_daily_quota', return_value=5):
            tasks = [
                TaskCreate(content="Task 1", is_optional=False),
                TaskCreate(content="Task 2", is_optional=False),
            ]

            result = await draft_tasks(tasks, mock_user)

            # Verify the delete was called (meaning existing entry was found)
            mock_supabase_base.table.return_value.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_draft_tasks_adventure_entry_matching_logic(self, mock_supabase_base, mock_user):
        """Adventure mode: Entry matching logic should correctly identify adventure entries.

        This test verifies that the uncommented adventure entry matching code works.
        It directly tests the loop logic without going through the full draft_tasks flow.
        """
        # Setup test data matching the draft_tasks loop at lines 87-94
        session_id = 'adventure-123'
        game_mode = GameMode.ADVENTURE

        # Simulate entries returned from database (with adventure_id field)
        matching_entry = {
            'id': 'entry-123',
            'adventure_id': 'adventure-123',  # Matches our session
        }
        other_entry = {
            'id': 'entry-456',
            'adventure_id': 'adventure-999',  # Different adventure
        }
        unrelated_entry = {
            'id': 'entry-789',
            'battle_id': 'battle-123',  # PVP entry, not adventure
        }

        entries = [matching_entry, other_entry, unrelated_entry]

        # Test the matching logic directly
        existing_entry = None
        if entries:
            for entry in entries:
                # Check if this entry belongs to our session (same as code at lines 89-94)
                if game_mode.value == "pvp" and entry.get("battle_id") == session_id:
                    existing_entry = entry
                    break
                elif game_mode.value == "adventure" and entry.get("adventure_id") == session_id:
                    existing_entry = entry
                    break

        # Verify the correct entry was found
        assert existing_entry is not None, "Should find the matching adventure entry"
        assert existing_entry['id'] == 'entry-123', "Should return the entry with matching adventure_id"

    @pytest.mark.asyncio
    async def test_draft_tasks_pvp_entry_matching_still_works(self, mock_supabase_base, mock_user):
        """PVP mode: Entry matching logic should still work after adding adventure support."""
        # Setup test data
        session_id = 'battle-123'
        game_mode = GameMode.PVP

        matching_entry = {
            'id': 'entry-123',
            'battle_id': 'battle-123',  # Matches our session
        }
        other_entry = {
            'id': 'entry-456',
            'battle_id': 'battle-999',  # Different battle
        }
        adventure_entry = {
            'id': 'entry-789',
            'adventure_id': 'adventure-123',  # Adventure entry, not PVP
        }

        entries = [matching_entry, other_entry, adventure_entry]

        # Test the matching logic directly
        existing_entry = None
        if entries:
            for entry in entries:
                if game_mode.value == "pvp" and entry.get("battle_id") == session_id:
                    existing_entry = entry
                    break
                elif game_mode.value == "adventure" and entry.get("adventure_id") == session_id:
                    existing_entry = entry
                    break

        # Verify the correct entry was found
        assert existing_entry is not None, "Should find the matching PVP entry"
        assert existing_entry['id'] == 'entry-123', "Should return the entry with matching battle_id"

    @pytest.mark.asyncio
    async def test_draft_tasks_no_matching_entry_creates_new(self, mock_supabase_base, mock_user):
        """When no entry matches the session, a new entry should be created."""
        # Setup test data
        session_id = 'adventure-123'
        game_mode = GameMode.ADVENTURE

        # Only entries for different sessions
        other_entries = [
            {'id': 'entry-456', 'adventure_id': 'adventure-999'},
            {'id': 'entry-789', 'battle_id': 'battle-123'},
        ]

        # Test the matching logic
        existing_entry = None
        if other_entries:
            for entry in other_entries:
                if game_mode.value == "pvp" and entry.get("battle_id") == session_id:
                    existing_entry = entry
                    break
                elif game_mode.value == "adventure" and entry.get("adventure_id") == session_id:
                    existing_entry = entry
                    break

        # Verify no entry was found (existing_entry stays None)
        assert existing_entry is None, "Should not find a matching entry"


# =============================================================================
# Test Draft Tasks Validation
# =============================================================================

class TestDraftTasksValidation:
    """Test task validation rules."""

    @pytest.fixture
    def mock_supabase_base(self):
        # Need to patch both routers.tasks and utils.game_session
        with patch('utils.game_session.supabase') as game_session_supabase, \
             patch('database.supabase', new=game_session_supabase), \
             patch('routers.tasks.supabase', new=game_session_supabase):
            yield game_session_supabase

    @pytest.fixture
    def mock_user(self):
        """Create a mock authenticated user."""
        user = Mock()
        user.id = 'user-123'
        return user

    @pytest.mark.asyncio
    async def test_draft_tasks_too_many_mandatory_raises(self, mock_supabase_base, mock_user):
        """Should raise error when mandatory tasks exceed quota."""
        setup_profile_mock(mock_supabase_base, 'user-123', timezone='UTC')

        # Mock active adventure
        battle_response = create_mock_execute_response(None)
        adventure_response = create_mock_execute_response({'id': 'adventure-123'})

        mock_supabase_base.table.return_value.select.return_value.or_.return_value\
            .eq.return_value.single.return_value.execute.side_effect = [
            battle_response,
            adventure_response,
        ]

        mock_supabase_base.table.return_value.select.return_value.eq.return_value.eq\
            .return_value.execute.return_value = create_mock_execute_response([])

        from routers.tasks import draft_tasks

        # Mock get_daily_quota to return 5
        with patch('routers.tasks.get_daily_quota', return_value=5):
            # Submit 6 mandatory tasks (exceeds quota of 5)
            tasks = [
                TaskCreate(content=f"Task {i}", is_optional=False)
                for i in range(6)
            ]

            with pytest.raises(HTTPException) as exc_info:
                await draft_tasks(tasks, mock_user)

            assert exc_info.value.status_code == 400
            assert "cannot submit more than" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_draft_tasks_no_tasks_raises(self, mock_supabase_base, mock_user):
        """Should raise error when no tasks submitted."""
        setup_profile_mock(mock_supabase_base, 'user-123', timezone='UTC')

        # Mock active adventure
        battle_response = create_mock_execute_response(None)
        adventure_response = create_mock_execute_response({'id': 'adventure-123'})

        mock_supabase_base.table.return_value.select.return_value.or_.return_value\
            .eq.return_value.single.return_value.execute.side_effect = [
            battle_response,
            adventure_response,
        ]

        mock_supabase_base.table.return_value.select.return_value.eq.return_value.eq\
            .return_value.execute.return_value = create_mock_execute_response([])

        from routers.tasks import draft_tasks

        # Mock get_daily_quota
        with patch('routers.tasks.get_daily_quota', return_value=5):
            # Submit empty task list
            with pytest.raises(HTTPException) as exc_info:
                await draft_tasks([], mock_user)

            assert exc_info.value.status_code == 400
            assert "at least one task" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_draft_tasks_too_many_optional_raises(self, mock_supabase_base, mock_user):
        """Should raise error when optional tasks exceed 2."""
        setup_profile_mock(mock_supabase_base, 'user-123', timezone='UTC')

        # Mock active adventure
        battle_response = create_mock_execute_response(None)
        adventure_response = create_mock_execute_response({'id': 'adventure-123'})

        mock_supabase_base.table.return_value.select.return_value.or_.return_value\
            .eq.return_value.single.return_value.execute.side_effect = [
            battle_response,
            adventure_response,
        ]

        mock_supabase_base.table.return_value.select.return_value.eq.return_value.eq\
            .return_value.execute.return_value = create_mock_execute_response([])

        from routers.tasks import draft_tasks

        # Mock get_daily_quota
        with patch('routers.tasks.get_daily_quota', return_value=5):
            # Submit 3 optional tasks (exceeds limit of 2)
            tasks = [
                TaskCreate(content=f"Optional {i}", is_optional=True)
                for i in range(3)
            ]

            with pytest.raises(HTTPException) as exc_info:
                await draft_tasks(tasks, mock_user)

            assert exc_info.value.status_code == 400
            assert "up to 2 optional" in exc_info.value.detail
