"""
Unit tests for battle helper functions.

Tests for the pure helper functions extracted from the battles router
to improve testability and maintainability.

REFACTOR-005: Phase 5 - Item 6.1
"""
import pytest
from datetime import date

from utils.battle_helpers import (
    extract_user_profiles,
    calculate_app_state,
    build_rival_intelligence,
    DEFAULT_USER_PROFILE,
    DEFAULT_RIVAL_PROFILE
)


class TestExtractUserProfiles:
    """Test profile extraction logic."""

    def test_extracts_correct_profiles_when_user1(self):
        """Should extract user1 as user, user2 as rival."""
        battle = {
            'id': 'battle-123',
            'user1_id': 'user-1',
            'user2_id': 'user-2',
            'user1': {'username': 'User1', 'level': 5, 'timezone': 'UTC'},
            'user2': {'username': 'User2', 'level': 3, 'timezone': 'UTC'}
        }
        user_profile, rival_profile, rival_id = extract_user_profiles(battle, 'user-1')

        assert user_profile['username'] == 'User1'
        assert user_profile['level'] == 5
        assert rival_profile['username'] == 'User2'
        assert rival_profile['level'] == 3
        assert rival_id == 'user-2'

    def test_extracts_correct_profiles_when_user2(self):
        """Should extract user2 as user, user1 as rival."""
        battle = {
            'id': 'battle-123',
            'user1_id': 'user-1',
            'user2_id': 'user-2',
            'user1': {'username': 'User1', 'level': 5, 'timezone': 'UTC'},
            'user2': {'username': 'User2', 'level': 3, 'timezone': 'UTC'}
        }
        user_profile, rival_profile, rival_id = extract_user_profiles(battle, 'user-2')

        assert user_profile['username'] == 'User2'
        assert user_profile['level'] == 3
        assert rival_profile['username'] == 'User1'
        assert rival_profile['level'] == 5
        assert rival_id == 'user-1'

    def test_returns_default_when_user_profile_is_null(self):
        """Should return default profile when user profile is None."""
        battle = {
            'id': 'battle-123',
            'user1_id': 'user-1',
            'user2_id': 'user-2',
            'user1': None,
            'user2': {'username': 'User2', 'level': 3, 'timezone': 'UTC'}
        }
        user_profile, rival_profile, rival_id = extract_user_profiles(battle, 'user-1')

        assert user_profile == DEFAULT_USER_PROFILE
        assert rival_profile['username'] == 'User2'
        assert rival_id == 'user-2'

    def test_returns_default_when_rival_profile_is_null(self):
        """Should return default rival profile when None."""
        battle = {
            'id': 'battle-123',
            'user1_id': 'user-1',
            'user2_id': 'user-2',
            'user1': {'username': 'User1', 'level': 5, 'timezone': 'UTC'},
            'user2': None
        }
        user_profile, rival_profile, rival_id = extract_user_profiles(battle, 'user-1')

        assert user_profile['username'] == 'User1'
        assert rival_profile == DEFAULT_RIVAL_PROFILE
        assert rival_id == 'user-2'

    def test_returns_defaults_when_both_profiles_null(self):
        """Should return defaults when both profiles are None."""
        battle = {
            'id': 'battle-123',
            'user1_id': 'user-1',
            'user2_id': 'user-2',
            'user1': None,
            'user2': None
        }
        user_profile, rival_profile, rival_id = extract_user_profiles(battle, 'user-1')

        assert user_profile == DEFAULT_USER_PROFILE
        assert rival_profile == DEFAULT_RIVAL_PROFILE


class TestCalculateAppState:
    """Test app state calculation logic."""

    def test_returns_pending_when_status_pending(self):
        """Should return PENDING_ACCEPTANCE for pending status."""
        state = calculate_app_state(
            'pending',
            date(2026, 1, 20),
            date(2026, 1, 25),
            date(2026, 1, 20)
        )
        assert state == 'PENDING_ACCEPTANCE'

    def test_returns_battle_end_when_status_completed(self):
        """Should return BATTLE_END for completed status."""
        state = calculate_app_state(
            'completed',
            date(2026, 1, 20),
            date(2026, 1, 25),
            date(2026, 1, 22)
        )
        assert state == 'BATTLE_END'

    def test_returns_pre_battle_when_today_before_start(self):
        """Should return PRE_BATTLE when today < start_date."""
        state = calculate_app_state(
            'active',
            date(2026, 1, 20),
            date(2026, 1, 25),
            date(2026, 1, 19)
        )
        assert state == 'PRE_BATTLE'

    def test_returns_in_battle_when_during_battle(self):
        """Should return IN_BATTLE when start <= today < end."""
        state = calculate_app_state(
            'active',
            date(2026, 1, 20),
            date(2026, 1, 25),
            date(2026, 1, 22)
        )
        assert state == 'IN_BATTLE'

    def test_returns_last_battle_day_on_final_day(self):
        """Should return LAST_BATTLE_DAY when today == end_date."""
        state = calculate_app_state(
            'active',
            date(2026, 1, 20),
            date(2026, 1, 25),
            date(2026, 1, 25)
        )
        assert state == 'LAST_BATTLE_DAY'

    def test_returns_battle_end_when_today_after_end(self):
        """Should return BATTLE_END when today > end_date."""
        state = calculate_app_state(
            'active',
            date(2026, 1, 20),
            date(2026, 1, 25),
            date(2026, 1, 26)
        )
        assert state == 'BATTLE_END'

    def test_returns_in_battle_on_start_date(self):
        """Should return IN_BATTLE when today == start_date (not end)."""
        state = calculate_app_state(
            'active',
            date(2026, 1, 20),
            date(2026, 1, 25),
            date(2026, 1, 20)
        )
        assert state == 'IN_BATTLE'


class TestBuildRivalIntelligence:
    """Test rival intelligence building."""

    def test_builds_complete_intelligence_dict(self):
        """Should build complete dict with all stats."""
        rival_profile = {
            'username': 'Rival',
            'level': 5,
            'battle_win_count': 3,
            'battle_count': 5,
            'total_xp_earned': 500,
            'completed_tasks': 20
        }
        intel = build_rival_intelligence(rival_profile, 5, 3)

        assert intel['username'] == 'Rival'
        assert intel['level'] == 5
        assert intel['tasks_total'] == 5
        assert intel['tasks_completed'] == 3
        assert intel['stats']['battle_wins'] == 3
        assert intel['stats']['battle_fought'] == 5
        assert intel['stats']['total_xp'] == 500
        assert intel['stats']['tasks_completed'] == 20
        assert intel['stats']['win_rate'] == '60.0%'

    def test_uses_defaults_when_profile_missing_fields(self):
        """Should use .get() defaults for missing fields."""
        intel = build_rival_intelligence({})

        assert intel['username'] == 'Unknown Rival'
        assert intel['level'] == 1
        assert intel['tasks_total'] == 0
        assert intel['tasks_completed'] == 0
        assert intel['stats']['battle_wins'] == 0
        assert intel['stats']['battle_fought'] == 0
        assert intel['stats']['level'] == 1
        assert intel['stats']['total_xp'] == 0
        assert intel['stats']['tasks_completed'] == 0
        assert intel['stats']['win_rate'] == '0.0%'

    def test_calculates_win_rate_correctly(self):
        """Should calculate win rate as percentage."""
        # Test various win rates (note: format_win_rate uses 1 decimal place)
        assert build_rival_intelligence({'battle_win_count': 0, 'battle_count': 0})['stats']['win_rate'] == '0.0%'
        assert build_rival_intelligence({'battle_win_count': 1, 'battle_count': 2})['stats']['win_rate'] == '50.0%'
        assert build_rival_intelligence({'battle_win_count': 3, 'battle_count': 3})['stats']['win_rate'] == '100.0%'
        assert build_rival_intelligence({'battle_win_count': 2, 'battle_count': 3})['stats']['win_rate'] == '66.7%'

    def test_includes_task_stats_when_provided(self):
        """Should include provided task stats."""
        rival_profile = {'username': 'Rival', 'level': 5}
        intel = build_rival_intelligence(rival_profile, total_tasks=8, completed_tasks=5)

        assert intel['tasks_total'] == 8
        assert intel['tasks_completed'] == 5

    def test_defaults_task_stats_to_zero(self):
        """Should default task stats to zero when not provided."""
        intel = build_rival_intelligence({'username': 'Rival'})

        assert intel['tasks_total'] == 0
        assert intel['tasks_completed'] == 0
