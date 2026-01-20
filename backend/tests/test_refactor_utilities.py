"""
Unit tests for shared utility functions.
Tests REFACTOR-001 (quota) and REFACTOR-002 (win rate).
"""
import pytest
from datetime import date


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

    def test_win_rate_negative_wins_handled(self):
        """Test that negative wins are handled (edge case)."""
        from utils.stats import calculate_win_rate

        # This shouldn't happen in practice but function should handle it
        result = calculate_win_rate(-1, 10)
        # Negative wins would give negative percentage
        assert result == -10.0


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

    def test_matches_tasks_py_implementation(self):
        """Test that utility matches tasks.py original implementation."""
        from utils.quota import get_daily_quota
        import hashlib

        test_date = date(2026, 6, 20)

        # Original tasks.py implementation (same logic)
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

    def test_matches_users_py_win_rate_formula(self):
        """Test that utility matches users.py original formula."""
        from utils.stats import calculate_win_rate

        # Original formula from users.py:
        # round((battle_win_count / battle_count) * 100, 1) if battle_count > 0 else 0
        battle_win_count = 3
        battle_count = 8

        expected = round((battle_win_count / battle_count) * 100, 1)
        result = calculate_win_rate(battle_win_count, battle_count)

        assert result == expected
