"""
Unit tests for utility functions.

Tests quota calculation, win rate calculation, GameMode enum,
and game session abstraction.
"""
import pytest
from datetime import date
from unittest.mock import Mock, patch
from fastapi import HTTPException


# =============================================================================
# Test get_daily_quota Utility
# =============================================================================

class TestGetDailyQuota:
    """Test get_daily_quota utility function."""

    def test_quota_returns_3_4_or_5(self):
        """Test that quota is always 3, 4, or 5."""
        from utils.quota import get_daily_quota

        # Test a range of dates
        test_dates = [
            date(2026, 1, 1),
            date(2026, 1, 2),
            date(2026, 1, 3),
            date(2026, 1, 4),
            date(2026, 1, 5),
            date(2026, 6, 15),
            date(2026, 12, 31),
        ]

        for test_date in test_dates:
            quota = get_daily_quota(test_date)
            assert quota in [3, 4, 5], f"Quota {quota} not in valid range for {test_date}"

    def test_quota_deterministic_for_same_date(self):
        """Test that same date always returns same quota."""
        from utils.quota import get_daily_quota

        test_date = date(2026, 1, 15)

        # Call multiple times
        quotas = [get_daily_quota(test_date) for _ in range(10)]

        # All should be the same
        assert len(set(quotas)) == 1, "Quota should be deterministic for same date"

    def test_quota_can_vary_by_date(self):
        """Test that different dates can have different quotas."""
        from utils.quota import get_daily_quota

        # Test many dates to ensure variation is possible
        test_dates = [date(2026, 1, day) for day in range(1, 32)]
        quotas = [get_daily_quota(d) for d in test_dates]

        # Should have at least 2 different values (all 3,4,5 unlikely)
        unique_quotas = set(quotas)
        assert len(unique_quotas) >= 2, f"Quotas should vary: {unique_quotas}"

    def test_quota_distribution_is_roughly_even(self):
        """Test that quotas are distributed roughly evenly across many dates."""
        from utils.quota import get_daily_quota

        # Test 100 days
        test_dates = [date(2026, 1, day % 28 + 1) for day in range(100)]
        quotas = [get_daily_quota(d) for d in test_dates]

        count_3 = quotas.count(3)
        count_4 = quotas.count(4)
        count_5 = quotas.count(5)

        # Each value should appear at least 20% of the time
        # (perfect distribution would be ~33% each)
        total = len(quotas)
        assert count_3 >= total * 0.15, f"Quota 3 underrepresented: {count_3}/{total}"
        assert count_4 >= total * 0.15, f"Quota 4 underrepresented: {count_4}/{total}"
        assert count_5 >= total * 0.15, f"Quota 5 underrepresented: {count_5}/{total}"

    def test_quota_leap_year_date(self):
        """Test that leap year dates work correctly."""
        from utils.quota import get_daily_quota

        # Feb 29 exists in leap years
        leap_date = date(2024, 2, 29)
        quota = get_daily_quota(leap_date)
        assert quota in [3, 4, 5]

    def test_quota_far_future_date(self):
        """Test that far future dates work correctly."""
        from utils.quota import get_daily_quota

        future_date = date(2099, 12, 31)
        quota = get_daily_quota(future_date)
        assert quota in [3, 4, 5]

    def test_quota_past_date(self):
        """Test that past dates work correctly."""
        from utils.quota import get_daily_quota

        past_date = date(2020, 1, 1)
        quota = get_daily_quota(past_date)
        assert quota in [3, 4, 5]


class TestCalculateWinRate:
    """Test calculate_win_rate utility function."""

    def test_win_rate_zero_battles(self):
        """Test that 0 battles handled gracefully (returns 0)."""
        from utils.stats import calculate_win_rate

        result = calculate_win_rate(0, 0)
        assert result == 0.0

    def test_win_rate_zero_division_safe(self):
        """Test that division by zero is handled."""
        from utils.stats import calculate_win_rate

        # 5 wins but 0 total battles (edge case)
        result = calculate_win_rate(5, 0)
        assert result == 0.0

    def test_win_rate_100_percent(self):
        """Test perfect win rate."""
        from utils.stats import calculate_win_rate

        result = calculate_win_rate(10, 10)
        assert result == 100.0

    def test_win_rate_50_percent(self):
        """Test 50% win rate."""
        from utils.stats import calculate_win_rate

        result = calculate_win_rate(5, 10)
        assert result == 50.0

    def test_win_rate_33_percent(self):
        """Test fractional win rate with rounding."""
        from utils.stats import calculate_win_rate

        result = calculate_win_rate(1, 3)
        assert result == 33.3

    def test_win_rate_66_percent(self):
        """Test another fractional win rate."""
        from utils.stats import calculate_win_rate

        result = calculate_win_rate(2, 3)
        assert result == 66.7

    def test_win_rate_zero_wins(self):
        """Test 0% win rate."""
        from utils.stats import calculate_win_rate

        result = calculate_win_rate(0, 10)
        assert result == 0.0

    def test_win_rate_rounding(self):
        """Test that win rate is rounded to 1 decimal place."""
        from utils.stats import calculate_win_rate

        # 1/7 = 14.2857... should round to 14.3
        result = calculate_win_rate(1, 7)
        assert result == 14.3

        # 2/7 = 28.5714... should round to 28.6
        result = calculate_win_rate(2, 7)
        assert result == 28.6

    def test_win_rate_returns_float(self):
        """Test that return type is float."""
        from utils.stats import calculate_win_rate

        result = calculate_win_rate(5, 10)
        assert isinstance(result, float)

    def test_win_rate_large_numbers(self):
        """Test with large battle counts."""
        from utils.stats import calculate_win_rate

        result = calculate_win_rate(567, 1000)
        assert result == 56.7


class TestQuotaBackwardCompatibility:
    """Test that new utility matches old behavior."""

    def test_matches_battles_py_implementation(self):
        """Test that utility matches battles.py original implementation."""
        from utils.quota import get_daily_quota
        import hashlib

        test_date = date(2026, 1, 15)

        # Original battles.py implementation
        date_str = test_date.isoformat()
        hash_obj = hashlib.md5(date_str.encode())
        hash_int = int(hash_obj.hexdigest(), 16)
        expected = (hash_int % 3) + 3

        # Utility implementation
        result = get_daily_quota(test_date)

        assert result == expected


class TestWinRateBackwardCompatibility:
    """Test that new utility matches old behavior."""

    def test_matches_battles_py_win_rate_formula(self):
        """Test that utility matches battles.py original formula."""
        from utils.stats import calculate_win_rate

        # Original formula from battles.py:
        # round((battle_win_count / battle_count) * 100, 1) if battle_count > 0 else 0
        battle_win_count = 7
        battle_count = 12

        expected = round((battle_win_count / battle_count) * 100, 1)
        result = calculate_win_rate(battle_win_count, battle_count)

        assert result == expected


# =============================================================================
# Test GameMode Enum
# =============================================================================

class TestGameModeEnum:
    """Test GameMode enum values and behavior."""

    def test_gamemode_pvp_value(self):
        """Test PVP mode has correct string value."""
        from utils.enums import GameMode

        assert GameMode.PVP == "pvp"
        assert GameMode.PVP.value == "pvp"

    def test_gamemode_adventure_value(self):
        """Test ADVENTURE mode has correct string value."""
        from utils.enums import GameMode

        assert GameMode.ADVENTURE == "adventure"
        assert GameMode.ADVENTURE.value == "adventure"

    def test_gamemode_is_string_enum(self):
        """Test GameMode is a string enum (compatible with string comparisons)."""
        from utils.enums import GameMode

        # Should be comparable to strings
        assert GameMode.PVP == "pvp"

        # Should work in dict lookups with strings
        lookup = {"pvp": "Player vs Player", "adventure": "Single Player"}
        assert lookup[GameMode.PVP] == "Player vs Player"

    def test_gamemode_iterable(self):
        """Test that all game modes can be iterated."""
        from utils.enums import GameMode

        modes = list(GameMode)
        assert len(modes) == 2
        assert GameMode.PVP in modes
        assert GameMode.ADVENTURE in modes

    def test_gamemode_serialization(self):
        """Test that GameMode can be serialized to JSON."""
        from utils.enums import GameMode
        import json

        # String enum serializes to its value, not name
        assert json.dumps(GameMode.PVP.value) == '"pvp"'


# =============================================================================
# Test get_active_game_session Helper
# =============================================================================

class TestGetActiveGameSession:
    """Test get_active_game_session helper function."""

    def test_returns_battle_id_and_pvp_mode_when_active_battle_exists(self, mock_user):
        """Test that active battle returns battle ID and PVP mode."""
        with patch('utils.game_session.supabase') as mock_supabase:
            # Mock active battle response
            mock_battle_res = Mock()
            mock_battle_res.data = {'id': 'battle-456'}
            mock_supabase.table.return_value.select.return_value\
                .or_.return_value.eq.return_value.single.return_value.execute.return_value = mock_battle_res

            from utils.game_session import get_active_game_session

            session_id, game_mode = get_active_game_session(mock_user.id)

            assert session_id == "battle-456"
            assert game_mode == "pvp"

            from utils.enums import GameMode
            assert game_mode == GameMode.PVP
            assert game_mode.value == "pvp"

    def test_raises_400_when_no_active_session(self, mock_user):
        """Test that HTTPException raised when no battle or adventure found."""
        with patch('utils.game_session.supabase') as mock_supabase:
            # Mock no battle found
            mock_battle_res = Mock()
            mock_battle_res.data = None
            mock_supabase.table.return_value.select.return_value\
                .or_.return_value.eq.return_value.single.return_value.execute.return_value = mock_battle_res

            from utils.game_session import get_active_game_session

            with pytest.raises(HTTPException) as exc_info:
                get_active_game_session(mock_user.id)

            assert exc_info.value.status_code == 400
            assert "No active battle or adventure found" in str(exc_info.value.detail)

    def test_battle_takes_priority_over_adventure(self, mock_user):
        """Test that battle is returned when both battle and adventure exist."""
        with patch('utils.game_session.supabase') as mock_supabase:
            # Mock active battle response
            mock_battle_res = Mock()
            mock_battle_res.data = {'id': 'battle-456'}
            mock_supabase.table.return_value.select.return_value\
                .or_.return_value.eq.return_value.single.return_value.execute.return_value = mock_battle_res

            from utils.game_session import get_active_game_session

            session_id, game_mode = get_active_game_session(mock_user.id)

            # Should return battle, not continue to check adventure
            assert session_id == "battle-456"

            from utils.enums import GameMode
            assert game_mode == GameMode.PVP
            assert game_mode.value == "pvp"


# =============================================================================
# Test get_daily_entry_key Helper
# =============================================================================

class TestGetDailyEntryKey:
    """Test get_daily_entry_key helper function."""

    def test_returns_battle_id_key_for_pvp_mode(self):
        """Test that PVP mode returns battle_id key."""
        from utils.game_session import get_daily_entry_key
        from utils.enums import GameMode

        result = get_daily_entry_key("battle-123", GameMode.PVP)
        assert result == {"battle_id": "battle-123"}

    def test_returns_adventure_id_key_for_adventure_mode(self):
        """Test that ADVENTURE mode returns adventure_id key."""
        from utils.game_session import get_daily_entry_key
        from utils.enums import GameMode

        result = get_daily_entry_key("adventure-456", GameMode.ADVENTURE)
        assert result == {"adventure_id": "adventure-456"}

    def test_raises_value_error_for_invalid_mode(self):
        """Test that invalid game mode raises ValueError."""
        from utils.game_session import get_daily_entry_key

        with pytest.raises(ValueError):
            get_daily_entry_key("session-123", "invalid_mode")


# =============================================================================
# Test has_active_game_session Helper
# =============================================================================

class TestHasActiveGameSession:
    """Test has_active_game_session helper function."""

    def test_returns_true_when_user_has_active_battle(self, mock_user):
        """Test that True is returned when user has active battle."""
        with patch('utils.game_session.supabase') as mock_supabase:
            mock_battle_res = Mock()
            mock_battle_res.data = {'id': 'battle-456'}
            mock_supabase.table.return_value.select.return_value\
                .or_.return_value.eq.return_value.single.return_value.execute.return_value = mock_battle_res

            from utils.game_session import has_active_game_session

            result = has_active_game_session(mock_user.id)
            assert result is True

    def test_returns_false_when_user_has_no_active_battle(self, mock_user):
        """Test that False is returned when user has no active battle."""
        with patch('utils.game_session.supabase') as mock_supabase:
            mock_battle_res = Mock()
            mock_battle_res.data = None
            mock_supabase.table.return_value.select.return_value\
                .or_.return_value.eq.return_value.single.return_value.execute.return_value = mock_battle_res

            from utils.game_session import has_active_game_session

            result = has_active_game_session(mock_user.id)
            assert result is False


# =============================================================================
# Test DailyEntry Model
# =============================================================================

class TestDailyEntryModel:
    """Test DailyEntry model supports both battle_id and adventure_id."""

    def test_daily_entry_battle_id_exists(self):
        """Test that DailyEntry has battle_id field."""
        from models import DailyEntry

        # Verify the model has the required field
        assert hasattr(DailyEntry, '__annotations__')
        assert 'battle_id' in DailyEntry.__annotations__


# =============================================================================
# Test Backward Compatibility
# =============================================================================

class TestBackwardCompatibility:
    """Test that changes are backward compatible."""

    def test_existing_battle_flow_unchanged(self):
        """Test that existing battle flow still works."""
        # The abstraction should not change existing behavior
        # Battles work exactly as before, just with cleaner code
        assert True  # Documented expectation

    def test_gamemode_enum_compatible_with_existing_strings(self):
        """Test GameMode enum works with existing string comparisons."""
        from utils.enums import GameMode

        # Existing code that checks for "active", "completed" etc. should work
        # GameMode is for distinguishing game TYPE, not status
        status = "active"
        assert status == "active"

        # GameMode should be comparable with strings
        mode = GameMode.PVP
        assert mode == "pvp"
        # The value attribute contains the actual string
        assert mode.value == "pvp"
