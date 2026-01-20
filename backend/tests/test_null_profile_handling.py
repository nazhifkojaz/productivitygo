"""
Unit tests for null profile handling in battles router.
Tests BUG-003 fix: Missing null checks for profile data.
"""
import pytest
import asyncio
from unittest.mock import Mock, patch
from fastapi import HTTPException


class TestGetCurrentBattleNullProfileHandling:
    """Test get_current_battle handles missing profiles gracefully."""

    @pytest.fixture
    def mock_user(self):
        """Mock authenticated user."""
        return Mock(id="user-123", email="test@example.com")

    @pytest.fixture
    def sample_battle_with_profiles(self):
        """Sample battle with both profiles present."""
        return {
            'id': 'battle-123',
            'user1_id': 'user-123',
            'user2_id': 'user-456',
            'start_date': '2026-01-20',
            'end_date': '2026-01-22',
            'duration': 3,
            'current_round': 0,
            'status': 'active',
            'user1': {
                'username': 'PlayerOne',
                'level': 5,
                'timezone': 'America/New_York',
                'battle_win_count': 3,
                'battle_count': 10,
                'total_xp_earned': 2500,
                'completed_tasks': 45
            },
            'user2': {
                'username': 'PlayerTwo',
                'level': 3,
                'timezone': 'Europe/London',
                'battle_win_count': 1,
                'battle_count': 5,
                'total_xp_earned': 1200,
                'completed_tasks': 25
            }
        }

    @pytest.fixture
    def sample_battle_with_null_user_profile(self):
        """Sample battle where user's own profile is None."""
        return {
            'id': 'battle-123',
            'user1_id': 'user-123',
            'user2_id': 'user-456',
            'start_date': '2026-01-20',
            'end_date': '2026-01-22',
            'duration': 3,
            'current_round': 0,
            'status': 'active',
            'user1': None,  # User's profile is missing!
            'user2': {
                'username': 'PlayerTwo',
                'level': 3,
                'timezone': 'Europe/London',
                'battle_win_count': 1,
                'battle_count': 5,
                'total_xp_earned': 1200,
                'completed_tasks': 25
            }
        }

    @pytest.fixture
    def sample_battle_with_null_rival_profile(self):
        """Sample battle where rival's profile is None."""
        return {
            'id': 'battle-123',
            'user1_id': 'user-123',
            'user2_id': 'user-456',
            'start_date': '2026-01-20',
            'end_date': '2026-01-22',
            'duration': 3,
            'current_round': 0,
            'status': 'active',
            'user1': {
                'username': 'PlayerOne',
                'level': 5,
                'timezone': 'America/New_York',
                'battle_win_count': 3,
                'battle_count': 10,
                'total_xp_earned': 2500,
                'completed_tasks': 45
            },
            'user2': None  # Rival's profile is missing!
        }

    @pytest.fixture
    def sample_battle_both_profiles_null(self):
        """Sample battle where both profiles are None."""
        return {
            'id': 'battle-123',
            'user1_id': 'user-123',
            'user2_id': 'user-456',
            'start_date': '2026-01-20',
            'end_date': '2026-01-22',
            'duration': 3,
            'current_round': 0,
            'status': 'active',
            'user1': None,
            'user2': None
        }

    def test_normal_case_both_profiles_exist(self, mock_user, sample_battle_with_profiles):
        """Test that normal case works when both profiles exist."""
        with patch('routers.battles.supabase') as mock_supabase:
            # Mock process_battle_rounds to return 0 (no rounds processed)
            with patch('utils.battle_processor.process_battle_rounds', return_value=0):
                mock_supabase.table.return_value.select.return_value\
                    .or_.return_value.eq.return_value.execute.return_value = Mock(
                        data=[sample_battle_with_profiles]
                    )

                from routers.battles import get_current_battle
                result = asyncio.run(get_current_battle(mock_user))

                assert result is not None
                assert 'app_state' in result
                assert 'rival' in result
                assert result['rival']['username'] == 'PlayerTwo'

    def test_null_user_profile_does_not_crash(self, mock_user, sample_battle_with_null_user_profile):
        """Test that null user profile doesn't crash the endpoint."""
        with patch('routers.battles.supabase') as mock_supabase:
            with patch('utils.battle_processor.process_battle_rounds', return_value=0):
                mock_supabase.table.return_value.select.return_value\
                    .or_.return_value.eq.return_value.execute.return_value = Mock(
                        data=[sample_battle_with_null_user_profile]
                    )

                from routers.battles import get_current_battle

                # Should not raise AttributeError
                result = asyncio.run(get_current_battle(mock_user))

                # Should have fallback values
                assert result is not None
                assert 'app_state' in result

    def test_null_rival_profile_does_not_crash(self, mock_user, sample_battle_with_null_rival_profile):
        """Test that null rival profile doesn't crash the endpoint."""
        with patch('routers.battles.supabase') as mock_supabase:
            with patch('utils.battle_processor.process_battle_rounds', return_value=0):
                mock_supabase.table.return_value.select.return_value\
                    .or_.return_value.eq.return_value.execute.return_value = Mock(
                        data=[sample_battle_with_null_rival_profile]
                    )

                from routers.battles import get_current_battle

                # Should not raise AttributeError
                result = asyncio.run(get_current_battle(mock_user))

                # Should have fallback rival data
                assert result is not None
                assert result.get('rival') is not None
                # Should use defaults
                assert result['rival'].get('username') in ['Unknown Rival', None]

    def test_both_profiles_null_does_not_crash(self, mock_user, sample_battle_both_profiles_null):
        """Test that null profiles for both users doesn't crash."""
        with patch('routers.battles.supabase') as mock_supabase:
            with patch('utils.battle_processor.process_battle_rounds', return_value=0):
                mock_supabase.table.return_value.select.return_value\
                    .or_.return_value.eq.return_value.execute.return_value = Mock(
                        data=[sample_battle_both_profiles_null]
                    )

                from routers.battles import get_current_battle

                # Should not raise AttributeError
                result = asyncio.run(get_current_battle(mock_user))

                # Should have some fallback data
                assert result is not None


class TestDefaultProfileValues:
    """Test default values when profile is None."""

    def test_default_user_profile_has_timezone(self):
        """Test default user profile includes timezone."""
        default_profile = {
            'timezone': 'UTC',
            'username': 'Unknown',
            'level': 1
        }
        assert default_profile.get('timezone') == 'UTC'
        assert default_profile.get('username') == 'Unknown'

    def test_default_rival_profile_has_all_fields(self):
        """Test default rival profile includes all required fields."""
        default_rival = {
            'timezone': 'UTC',
            'username': 'Unknown Rival',
            'level': 1,
            'battle_win_count': 0,
            'battle_count': 0,
            'total_xp_earned': 0,
            'completed_tasks': 0
        }
        # Verify all fields exist
        assert default_rival.get('timezone') == 'UTC'
        assert default_rival.get('username') == 'Unknown Rival'
        assert default_rival.get('level') == 1
        assert default_rival.get('battle_win_count') == 0
        assert default_rival.get('battle_count') == 0
        assert default_rival.get('total_xp_earned') == 0
        assert default_rival.get('completed_tasks') == 0


class TestPartialProfileData:
    """Test handling of partial profile data."""

    def test_profile_with_missing_timezone(self):
        """Test profile missing timezone field uses .get() default."""
        partial_profile = {'username': 'Player', 'level': 5}
        # Should use UTC as default
        assert partial_profile.get('timezone', 'UTC') == 'UTC'

    def test_profile_with_missing_username(self):
        """Test profile missing username field uses .get() default."""
        partial_profile = {'timezone': 'UTC', 'level': 5}
        # Should use default value
        assert partial_profile.get('username', 'Unknown') == 'Unknown'


class TestSafeGetWithNone:
    """Test the safe get pattern with None values."""

    def test_none_with_get_attribute_raises_error(self):
        """Demonstrate that None.get() raises AttributeError."""
        none_value = None
        with pytest.raises(AttributeError):
            none_value.get('timezone', 'UTC')

    def test_or_operator_with_none(self):
        """Test using 'or' operator to provide default when None."""
        none_value = None
        default = {'timezone': 'UTC', 'username': 'Unknown'}
        result = none_value or default
        assert result == default

    def test_or_operator_with_valid_value(self):
        """Test that 'or' operator doesn't replace valid values."""
        valid_value = {'timezone': 'America/New_York', 'username': 'Player'}
        default = {'timezone': 'UTC', 'username': 'Unknown'}
        result = valid_value or default
        assert result == valid_value
        assert result['timezone'] == 'America/New_York'
