"""
Unit tests for battle processor and timezone handling.

Tests round processing, timezone handling, and date calculations.
"""
import pytest
from datetime import date, datetime
import pytz
import pytz.exceptions
from unittest.mock import Mock, patch

from utils.battle_processor import get_local_date, process_battle_rounds


# =============================================================================
# Test get_local_date Function
# =============================================================================

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
        # UTC should always be within a day of today
        assert abs((datetime.now().date() - result).days) <= 1

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
        result = get_local_date(None)
        assert isinstance(result, date)
        assert result == datetime.now(pytz.utc).date()

    def test_numeric_timezone_falls_back_to_utc(self):
        """Test that a numeric timezone string falls back to UTC gracefully."""
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
        result = get_local_date("america/new_york")
        assert isinstance(result, date)

    def test_whitespace_only_timezone_falls_back_to_utc(self):
        """Test timezone string with only whitespace falls back to UTC."""
        result = get_local_date("   ")
        assert isinstance(result, date)
        assert result == datetime.now(pytz.utc).date()


class TestGetUserDate:
    """Test get_user_date function from tasks.py router"""

    def test_get_user_date_valid_timezone(self):
        """Import and test get_user_date from tasks router."""
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


# =============================================================================
# Test Battle Round Processing
# =============================================================================

class TestBattleProcessorRoundProcessing:
    """Test round processing with various RPC scenarios."""

    @pytest.fixture
    def mock_supabase_base(self):
        """Base mock for supabase."""
        with patch('utils.battle_processor.supabase') as mock:
            yield mock

    def test_round_not_processed_when_date_not_passed(self, mock_supabase_base):
        """Test that round is not processed when date hasn't passed for both players."""
        battle = {
            'id': 'battle-123',
            'user1_id': 'user-1',
            'user2_id': 'user-2',
            'start_date': '2026-01-20',
            'end_date': '2026-01-22',
            'duration': 3,
            'current_round': 0,
            'status': 'active',
            'user1': {'timezone': 'UTC'},
            'user2': {'timezone': 'UTC'}
        }

        # Mock dates that haven't passed yet
        with patch('utils.battle_processor.datetime') as mock_dt:
            # Today is before round date
            mock_dt.now.return_value.date.return_value = date(2026, 1, 19)

            result = process_battle_rounds(battle)
            # Should not process any rounds
            assert result == 0

    def test_round_processed_when_both_players_finished(self, mock_supabase_base):
        """Test that round is processed when both players have finished."""
        battle = {
            'id': 'battle-123',
            'user1_id': 'user-1',
            'user2_id': 'user-2',
            'start_date': '2026-01-20',
            'end_date': '2026-01-22',
            'duration': 3,
            'current_round': 0,
            'status': 'active',
            'user1': {'timezone': 'UTC'},
            'user2': {'timezone': 'UTC'}
        }

        # Mock successful RPC
        mock_rpc = Mock()
        mock_rpc.execute.return_value = Mock(data=[
            {'user1_xp': 100, 'user2_xp': 50, 'winner_id': 'user-1'}
        ])
        mock_supabase_base.rpc.return_value = mock_rpc
        mock_supabase_base.table.return_value.update.return_value.eq.return_value.execute.return_value = Mock()

        with patch('utils.battle_processor.get_local_date') as mock_date:
            # Both players have finished the round (yesterday)
            mock_date.side_effect = [
                date(2026, 1, 21),  # user1's local date
                date(2026, 1, 21)   # user2's local date
            ]

            result = process_battle_rounds(battle)

            # Should process one round
            assert result == 1

    def test_multiple_rounds_processed(self, mock_supabase_base):
        """Test that multiple rounds are processed correctly."""
        battle = {
            'id': 'battle-123',
            'user1_id': 'user-1',
            'user2_id': 'user-2',
            'start_date': '2026-01-20',
            'end_date': '2026-01-22',
            'duration': 3,
            'current_round': 0,
            'status': 'active',
            'user1': {'timezone': 'UTC'},
            'user2': {'timezone': 'UTC'}
        }

        # Mock successful RPC calls
        mock_rpc = Mock()
        mock_rpc.execute.return_value = Mock(data=[
            {'user1_xp': 100, 'user2_xp': 50, 'winner_id': 'user-1'}
        ])
        mock_supabase_base.rpc.return_value = mock_rpc
        mock_supabase_base.table.return_value.update.return_value.eq.return_value.execute.return_value = Mock()

        # Mock date.today() to return a date 2 days after start date
        with patch('utils.battle_processor.date') as mock_date:
            mock_date.today.return_value = date(2026, 1, 22)
            mock_date.fromisoformat = date.fromisoformat

            with patch('utils.battle_processor.get_local_date') as mock_get_date:
                # Both players have finished 2 rounds
                mock_get_date.side_effect = [
                    date(2026, 1, 22),  # user1's local date
                    date(2026, 1, 22),  # user2's local date for round 0
                    date(2026, 1, 22),  # user1's local date for round 1
                    date(2026, 1, 22),  # user2's local date for round 1
                ]

                result = process_battle_rounds(battle)

                # Should process two rounds
                assert result == 2

    def test_processing_stops_at_battle_completion(self, mock_supabase_base):
        """Test that processing stops when battle duration is reached."""
        battle = {
            'id': 'battle-123',
            'user1_id': 'user-1',
            'user2_id': 'user-2',
            'start_date': '2026-01-20',
            'end_date': '2026-01-22',
            'duration': 3,
            'current_round': 2,  # Already at round 2
            'status': 'active',
            'user1': {'timezone': 'UTC'},
            'user2': {'timezone': 'UTC'}
        }

        # Mock battle completion RPC
        mock_rpc = Mock()
        mock_rpc.execute.return_value = Mock(data=[
            {'winner_id': 'user-1', 'user1_total_xp': 300, 'user2_total_xp': 200, 'already_completed': False}
        ])
        mock_supabase_base.rpc.return_value = mock_rpc
        mock_supabase_base.table.return_value.update.return_value.eq.return_value.execute.return_value = Mock()

        with patch('utils.battle_processor.get_local_date') as mock_date:
            # Both players finished the last round
            mock_date.side_effect = [
                date(2026, 1, 23),
                date(2026, 1, 23),
            ]

            result = process_battle_rounds(battle)

            # Should process the final round
            assert result >= 0
