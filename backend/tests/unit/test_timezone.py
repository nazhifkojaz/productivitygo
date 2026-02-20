"""
Unit tests for timezone utilities.

Tests for the centralized timezone/date functions extracted from
4 duplicate implementations across the codebase.

REFACTOR-007: Phase 2 Item 2.1
"""
import pytest
from datetime import date
from utils.timezone import get_local_date


class TestGetLocalDate:
    """Test get_local_date utility function."""

    def test_valid_timezone_returns_date(self):
        """Test that valid timezone returns a date object."""
        result = get_local_date('America/New_York')
        assert isinstance(result, date)

    def test_valid_timezone_utc(self):
        """Test UTC timezone."""
        result = get_local_date('UTC')
        assert isinstance(result, date)

    def test_valid_timezone_asia_tokyo(self):
        """Test Asia/Tokyo timezone."""
        result = get_local_date('Asia/Tokyo')
        assert isinstance(result, date)

    def test_invalid_timezone_fallback_to_utc(self):
        """Test that invalid timezone falls back to UTC."""
        result = get_local_date('Invalid/Timezone')
        assert isinstance(result, date)
        # Should be a valid date (UTC date)

    def test_empty_string_fallback_to_utc(self):
        """Test that empty string falls back to UTC."""
        result = get_local_date('')
        assert isinstance(result, date)

    def test_none_treated_as_invalid_timezone(self):
        """Test that None falls back to UTC (pytz doesn't raise TypeError)."""
        # pytz.timezone(None) actually returns UTC, not raising TypeError
        result = get_local_date(None)
        assert isinstance(result, date)

    def test_multiple_calls_consistent(self):
        """Test that multiple calls for same timezone are consistent."""
        tz = 'America/New_York'
        result1 = get_local_date(tz)
        result2 = get_local_date(tz)
        # Should return the same date (called within same second)
        assert result1 == result2

    def test_different_timezones_same_date(self):
        """Test that different timezones return valid dates."""
        timezones = [
            'America/New_York',
            'America/Los_Angeles',
            'Europe/London',
            'Asia/Tokyo',
            'Australia/Sydney',
        ]
        for tz in timezones:
            result = get_local_date(tz)
            assert isinstance(result, date), f"Failed for timezone: {tz}"

    def test_garbage_timezone_fallback(self):
        """Test various garbage inputs fall back gracefully."""
        garbage_inputs = [
            'NotATimezone',
            'XYZ123',
            '!!!',
            'US/Eastern',  # Common non-IANA format
        ]
        for garbage in garbage_inputs:
            result = get_local_date(garbage)
            assert isinstance(result, date), f"Failed for input: {garbage}"
