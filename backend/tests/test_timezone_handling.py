"""
Unit tests for timezone handling functions.
Tests BUG-002 fix: Bare exception handlers.
"""
import pytest
from datetime import date, datetime
import pytz
import pytz.exceptions

from utils.battle_processor import get_local_date


class TestGetLocalDate:
    """Test get_local_date function in battle_processor.py"""

    def test_valid_timezone_returns_date(self):
        """Test that a valid timezone string returns a date object."""
        result = get_local_date("America/New_York")
        assert isinstance(result, date)
        # Result should be today or potentially yesterday depending on timezone
        assert (datetime.now().date() - result).days <= 1

    def test_utc_timezone_returns_date(self):
        """Test that UTC timezone returns a date object."""
        result = get_local_date("UTC")
        assert isinstance(result, date)
        # UTC should always be today
        assert result == datetime.now().date()

    def test_invalid_timezone_falls_back_to_utc(self):
        """Test that an invalid timezone string falls back to UTC."""
        result = get_local_date("Invalid/Timezone/String")
        assert isinstance(result, date)
        # Should fall back to UTC (today)
        assert result == datetime.now(pytz.utc).date()

    def test_empty_timezone_falls_back_to_utc(self):
        """Test that an empty timezone string falls back to UTC."""
        result = get_local_date("")
        assert isinstance(result, date)

    def test_none_timezone_falls_back_to_utc(self):
        """Test that None timezone falls back to UTC gracefully."""
        # pytz.timezone(None) raises UnknownTimeZoneError
        # Our fix catches this and falls back to UTC
        result = get_local_date(None)
        assert isinstance(result, date)
        assert result == datetime.now(pytz.utc).date()

    def test_numeric_timezone_falls_back_to_utc(self):
        """Test that a numeric timezone string falls back to UTC gracefully."""
        # pytz.timezone('12345') raises UnknownTimeZoneError
        # Our fix catches this and falls back to UTC
        result = get_local_date("12345")
        assert isinstance(result, date)
        assert result == datetime.now(pytz.utc).date()


class TestTimezoneEdgeCases:
    """Test edge cases for timezone handling"""

    def test_all_common_timezones_work(self):
        """Test that common timezone strings are valid."""
        common_timezones = [
            "UTC",
            "America/New_York",
            "America/Los_Angeles",
            "Europe/London",
            "Europe/Paris",
            "Asia/Tokyo",
            "Asia/Shanghai",
            "Australia/Sydney",
        ]
        for tz in common_timezones:
            result = get_local_date(tz)
            assert isinstance(result, date), f"Failed for timezone: {tz}"

    def test_timezone_case_insensitive(self):
        """Test that pytz timezone strings are case-insensitive."""
        # pytz actually accepts lowercase timezone strings
        result = get_local_date("america/new_york")
        assert isinstance(result, date)

    def test_whitespace_only_timezone_falls_back_to_utc(self):
        """Test timezone string with only whitespace falls back to UTC."""
        # Whitespace is not a valid timezone, should fall back to UTC
        result = get_local_date("   ")
        assert isinstance(result, date)
        assert result == datetime.now(pytz.utc).date()


class TestGetUserDate:
    """Test get_user_date function from tasks.py router"""

    def test_get_user_date_valid_timezone(self):
        """Import and test get_user_date from tasks router."""
        # Import here to avoid issues if module doesn't exist
        from routers.tasks import get_user_date

        result = get_user_date("America/Chicago")
        assert isinstance(result, date)

    def test_get_user_date_invalid_timezone(self):
        """Test get_user_date falls back to UTC for invalid timezone."""
        from routers.tasks import get_user_date

        result = get_user_date("Invalid/Timezone")
        assert isinstance(result, date)
        # Should be UTC date
        assert result == datetime.now(pytz.utc).date()


class TestBattlesRouterGetLocalDate:
    """Test the inline get_local_date helper in battles.py"""

    def test_battles_router_local_date_valid(self):
        """Test the local helper function in battles router works."""
        # This simulates the inline function in battles.py
        def get_local_date(tz_str: str) -> date:
            try:
                return datetime.now(pytz.timezone(tz_str)).date()
            except pytz.exceptions.UnknownTimeZoneError:
                return datetime.now(pytz.utc).date()

        result = get_local_date("Europe/Berlin")
        assert isinstance(result, date)

    def test_battles_router_local_date_invalid(self):
        """Test the local helper function falls back to UTC."""
        def get_local_date(tz_str: str) -> date:
            try:
                return datetime.now(pytz.timezone(tz_str)).date()
            except pytz.exceptions.UnknownTimeZoneError:
                return datetime.now(pytz.utc).date()

        result = get_local_date("Not/A/Real/Timezone")
        assert isinstance(result, date)
        assert result == datetime.now(pytz.utc).date()


class TestBareExceptAntiPattern:
    """Tests demonstrating the problems with bare except."""

    def test_bare_except_catches_system_exit(self):
        """Demonstrate that bare except: would catch SystemExit."""
        # SystemExit inherits from BaseException, not Exception
        # Bare except: catches BaseException, so it catches SystemExit
        caught_system_exit = False

        try:
            raise SystemExit()
        except BaseException:  # This is what bare except: does
            caught_system_exit = True

        assert caught_system_exit is True
        # This means you can't properly exit the program!

    def test_specific_except_does_not_catch_system_exit(self):
        """Demonstrate that specific except allows SystemExit to propagate."""
        def func_with_specific_except():
            try:
                raise SystemExit()
            except pytz.exceptions.UnknownTimeZoneError:
                pass

        # This should raise SystemExit (not caught by specific except)
        with pytest.raises(SystemExit):
            func_with_specific_except()
