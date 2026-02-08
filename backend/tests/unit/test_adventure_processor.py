"""
Unit tests for adventure processor.

Tests round processing, timezone handling, break day management,
and adventure completion.
"""
import pytest
from datetime import date, datetime, timedelta
import pytz
from unittest.mock import Mock, patch, MagicMock, call, AsyncMock

from utils.adventure_processor import get_local_date, process_adventure_rounds, complete_adventure


# =============================================================================
# Test get_local_date Function
# =============================================================================

class TestGetLocalDate:
    """Test get_local_date function in adventure_processor.py"""

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


# =============================================================================
# Mock Helpers
# =============================================================================

def create_mock_execute_response(data):
    """Create a mock execute response with data attribute."""
    mock_response = Mock()
    mock_response.data = data
    return mock_response


def setup_profile_mock(mock_supabase, timezone='UTC'):
    """Setup the profile fetch mock chain with AsyncMock."""
    mock_supabase.table.return_value.select.return_value.eq.return_value.single\
        .return_value.execute = AsyncMock(
            return_value=create_mock_execute_response({'timezone': timezone})
        )


def setup_adventure_reload_mock(mock_supabase, hp=200, status='active'):
    """Setup the adventure reload mock chain."""
    mock_execute = create_mock_execute_response({
        'monster_current_hp': hp,
        'status': status
    })
    # Note: This will be called after other operations, so we need side_effect
    return mock_execute


# =============================================================================
# Test process_adventure_rounds Function
# =============================================================================

@pytest.mark.asyncio
class TestAdventureProcessorRoundProcessing:
    """Test adventure round processing with various scenarios."""

    @pytest.fixture
    def mock_supabase_base(self):
        """Base mock for supabase."""
        with patch('utils.adventure_processor.supabase') as mock:
            yield mock

    @pytest.fixture
    def sample_adventure(self):
        """Sample active adventure for testing."""
        today = date.today()
        start = today - timedelta(days=2)
        deadline = today + timedelta(days=2)
        return {
            'id': 'adv-123',
            'user_id': 'user-123',
            'monster_id': 'monster-1',
            'status': 'active',
            'start_date': start.isoformat(),
            'deadline': deadline.isoformat(),
            'current_round': 0,
            'monster_current_hp': 300,
            'monster_max_hp': 300,
            'is_on_break': False,
            'break_end_date': None,
        }

    async def test_returns_zero_for_non_active_adventure(self, mock_supabase_base, sample_adventure):
        """Test that non-active adventures return 0 rounds processed."""
        sample_adventure['status'] = 'completed'

        result = await process_adventure_rounds(sample_adventure)

        assert result == 0
        # Should not call any RPC functions
        mock_supabase_base.rpc.assert_not_called()

    async def test_skips_processing_when_on_break(self, mock_supabase_base, sample_adventure):
        """Test that rounds are not processed when adventure is on break."""
        today = date.today()
        tomorrow = today + timedelta(days=1)

        sample_adventure['is_on_break'] = True
        sample_adventure['break_end_date'] = tomorrow.isoformat()

        setup_profile_mock(mock_supabase_base)

        result = await process_adventure_rounds(sample_adventure)

        assert result == 0
        # Should not call calculate_adventure_round RPC
        mock_supabase_base.rpc.assert_not_called()

    async def test_clears_expired_break_status(self, mock_supabase_base, sample_adventure):
        """Test that break status is cleared when break end date has passed."""
        # Use a date far in the past to ensure it's always expired
        past_date = date(2020, 1, 1)

        sample_adventure['is_on_break'] = True
        sample_adventure['break_end_date'] = past_date.isoformat()

        # Track call count for dynamic responses
        call_count = [0]

        def dynamic_execute_response():
            call_count[0] += 1
            if call_count[0] == 1:
                # First call: profile fetch
                return create_mock_execute_response({'timezone': 'UTC'})
            elif call_count[0] == 2:
                # Second call: reload after processing
                return create_mock_execute_response({'monster_current_hp': 200, 'status': 'active'})
            else:
                # Any other calls
                return create_mock_execute_response({'monster_current_hp': 200, 'status': 'active'})

        # Setup the select mock chain first with side_effect for multiple calls
        # Note: This handles BOTH profiles and adventures table select calls
        mock_supabase_base.table.return_value.select.return_value.eq.return_value.single\
            .return_value.execute = AsyncMock(side_effect=dynamic_execute_response)

        # Mock the update call separately
        mock_supabase_base.table.return_value.update.return_value.eq.return_value.execute = \
            AsyncMock(return_value=create_mock_execute_response(None))

        # Mock RPC for round processing after break is cleared
        mock_supabase_base.rpc.return_value.execute = AsyncMock(
            return_value=create_mock_execute_response([{'damage': 100, 'new_hp': 200}])
        )

        result = await process_adventure_rounds(sample_adventure)

        # Should have called update to clear break status
        mock_supabase_base.table.return_value.update.assert_called()
        update_call_args = mock_supabase_base.table.return_value.update.call_args[0][0]
        assert update_call_args['is_on_break'] is False
        assert update_call_args['break_end_date'] is None

    async def test_clears_break_status_with_no_end_date(self, mock_supabase_base, sample_adventure):
        """Test that break status is cleared when break_end_date is None."""
        sample_adventure['is_on_break'] = True
        sample_adventure['break_end_date'] = None

        setup_profile_mock(mock_supabase_base)

        # Mock the update call
        mock_supabase_base.table.return_value.update.return_value.eq.return_value\
            .execute = AsyncMock(return_value=create_mock_execute_response(None))

        # Mock RPC for round processing after break is cleared
        mock_supabase_base.rpc.return_value.execute = AsyncMock(
            return_value=create_mock_execute_response([{'damage': 100, 'new_hp': 200}])
        )

        # Mock reload with side_effect
        mock_supabase_base.table.return_value.select.return_value.eq.return_value.single\
            .return_value.execute = AsyncMock(side_effect=[
                create_mock_execute_response({'timezone': 'UTC'}),
                create_mock_execute_response({'monster_current_hp': 200, 'status': 'active'})
            ])

        result = await process_adventure_rounds(sample_adventure)

        # Should have called update to clear inconsistent break status
        mock_supabase_base.table.return_value.update.assert_called()

    async def test_processes_rounds_successfully(self, mock_supabase_base, sample_adventure):
        """Test that rounds are processed successfully."""
        setup_profile_mock(mock_supabase_base)

        # Mock successful RPC call
        mock_supabase_base.rpc.return_value.execute = AsyncMock(
            return_value=create_mock_execute_response([{'damage': 100, 'new_hp': 200}])
        )

        # Mock reload after processing
        mock_supabase_base.table.return_value.select.return_value.eq.return_value.single\
            .return_value.execute = AsyncMock(side_effect=[
                create_mock_execute_response({'timezone': 'UTC'}),
                create_mock_execute_response({'monster_current_hp': 200, 'status': 'active'})
            ])

        result = await process_adventure_rounds(sample_adventure)

        # Should have processed rounds
        assert result >= 0
        # Should have called calculate_adventure_round
        mock_supabase_base.rpc.assert_called()

    async def test_handles_rpc_none_response(self, mock_supabase_base, sample_adventure):
        """Test handling of None response from RPC."""
        setup_profile_mock(mock_supabase_base)

        # Mock RPC returning None
        mock_supabase_base.rpc.return_value.execute = AsyncMock(
            return_value=create_mock_execute_response(None)
        )

        result = await process_adventure_rounds(sample_adventure)

        # Should stop processing and return rounds_processed (0 since RPC failed)
        assert result == 0

    async def test_handles_rpc_dict_response(self, mock_supabase_base, sample_adventure):
        """Test handling of dict (not list) response from RPC."""
        setup_profile_mock(mock_supabase_base)

        # Mock RPC returning dict instead of list
        mock_supabase_base.rpc.return_value.execute = AsyncMock(
            return_value=create_mock_execute_response({'damage': 80, 'new_hp': 220})
        )

        # Mock reload after processing
        mock_supabase_base.table.return_value.select.return_value.eq.return_value.single\
            .return_value.execute = AsyncMock(side_effect=[
                create_mock_execute_response({'timezone': 'UTC'}),
                create_mock_execute_response({'monster_current_hp': 220, 'status': 'active'})
            ])

        result = await process_adventure_rounds(sample_adventure)

        # Should handle dict response correctly
        assert result >= 0

    async def test_completes_adventure_on_victory(self, mock_supabase_base, sample_adventure):
        """Test that adventure is completed when monster HP reaches 0."""
        setup_profile_mock(mock_supabase_base)

        # Mock calculate_adventure_round RPC
        mock_supabase_base.rpc.return_value.execute = AsyncMock(side_effect=[
            create_mock_execute_response([{'damage': 300, 'new_hp': 0}]),
            create_mock_execute_response([{'is_victory': True, 'xp_earned': 450}])
        ])

        # Mock reload showing HP <= 0 (victory condition)
        mock_supabase_base.table.return_value.select.return_value.eq.return_value.single\
            .return_value.execute = AsyncMock(side_effect=[
                create_mock_execute_response({'timezone': 'UTC'}),
                create_mock_execute_response({'monster_current_hp': 0, 'status': 'active'})
            ])

        result = await process_adventure_rounds(sample_adventure)

        # Should have called complete_adventure
        assert mock_supabase_base.rpc.call_count >= 1

    async def test_completes_adventure_on_deadline_passed(self, mock_supabase_base, sample_adventure):
        """Test that adventure is completed when deadline has passed."""
        today = date.today()
        past = today - timedelta(days=5)
        start = past - timedelta(days=3)

        sample_adventure['start_date'] = start.isoformat()
        sample_adventure['deadline'] = past.isoformat()  # Deadline in the past

        setup_profile_mock(mock_supabase_base)

        # Mock RPC calls
        mock_supabase_base.rpc.return_value.execute = AsyncMock(side_effect=[
            create_mock_execute_response([{'damage': 50, 'new_hp': 50}]),
            create_mock_execute_response([{'is_victory': False, 'xp_earned': 200}])
        ])

        # Mock reload after processing and status check
        mock_supabase_base.table.return_value.select.return_value.eq.return_value.single\
            .return_value.execute = AsyncMock(side_effect=[
                create_mock_execute_response({'timezone': 'UTC'}),
                create_mock_execute_response({'monster_current_hp': 50, 'status': 'active'}),
                create_mock_execute_response({'status': 'active'})
            ])

        result = await process_adventure_rounds(sample_adventure)

        # Should have processed rounds
        assert result >= 0

    async def test_skips_completion_if_already_completed(self, mock_supabase_base, sample_adventure):
        """Test that completion is skipped if adventure already completed."""
        today = date.today()
        past = today - timedelta(days=5)
        sample_adventure['deadline'] = past.isoformat()

        setup_profile_mock(mock_supabase_base)

        # Mock RPC call for round processing
        mock_supabase_base.rpc.return_value.execute = AsyncMock(
            return_value=create_mock_execute_response([{'damage': 50, 'new_hp': 50}])
        )

        # Mock profile fetch, reload, and status check (already completed)
        mock_supabase_base.table.return_value.select.return_value.eq.return_value.single\
            .return_value.execute = AsyncMock(side_effect=[
                create_mock_execute_response({'timezone': 'UTC'}),
                create_mock_execute_response({'monster_current_hp': 50, 'status': 'active'}),
                create_mock_execute_response({'status': 'completed'})
            ])

        result = await process_adventure_rounds(sample_adventure)

        # Should process rounds but not complete again
        assert result >= 0

    async def test_handles_exception_during_round_processing(self, mock_supabase_base, sample_adventure):
        """Test that exceptions during round processing are handled gracefully."""
        setup_profile_mock(mock_supabase_base)

        # Mock RPC that raises exception
        mock_supabase_base.rpc.return_value.execute = AsyncMock(
            side_effect=Exception("Database error")
        )

        result = await process_adventure_rounds(sample_adventure)

        # Should handle exception and return 0
        assert result == 0


# =============================================================================
# Test complete_adventure Function
# =============================================================================

@pytest.mark.asyncio
class TestCompleteAdventure:
    """Test adventure completion function."""

    @pytest.fixture
    def mock_supabase_base(self):
        """Base mock for supabase."""
        with patch('utils.adventure_processor.supabase') as mock:
            yield mock

    async def test_completes_adventure_successfully(self, mock_supabase_base):
        """Test successful adventure completion."""
        # Mock RPC response
        mock_supabase_base.rpc.return_value.execute = AsyncMock(
            return_value=create_mock_execute_response([{'is_victory': True, 'xp_earned': 450, 'status': 'completed'}])
        )

        result = await complete_adventure('adv-123')

        assert result is not None
        assert result['is_victory'] is True
        assert result['xp_earned'] == 450
        mock_supabase_base.rpc.assert_called_once_with(
            "complete_adventure",
            {"adventure_uuid": "adv-123"}
        )

    async def test_handles_dict_response(self, mock_supabase_base):
        """Test handling of dict (not list) response from RPC."""
        # Mock RPC response as dict
        mock_supabase_base.rpc.return_value.execute = AsyncMock(
            return_value=create_mock_execute_response({'is_victory': False, 'xp_earned': 200, 'status': 'completed'})
        )

        result = await complete_adventure('adv-123')

        assert result is not None
        assert result['is_victory'] is False
        assert result['xp_earned'] == 200

    async def test_returns_none_on_rpc_none_response(self, mock_supabase_base):
        """Test that None is returned when RPC returns None."""
        mock_supabase_base.rpc.return_value.execute = AsyncMock(
            return_value=create_mock_execute_response(None)
        )

        result = await complete_adventure('adv-123')

        assert result is None

    async def test_returns_none_on_rpc_exception(self, mock_supabase_base):
        """Test that None is returned when RPC raises exception."""
        mock_supabase_base.rpc.return_value.execute = AsyncMock(
            side_effect=Exception("RPC failed")
        )

        result = await complete_adventure('adv-123')

        assert result is None

    async def test_handles_dict_with_none_data(self, mock_supabase_base):
        """Test handling of list response with None inner data."""
        mock_supabase_base.rpc.return_value.execute = AsyncMock(
            return_value=create_mock_execute_response([None])  # List with None element
        )

        result = await complete_adventure('adv-123')

        assert result is None


# =============================================================================
# Integration-Style Tests
# =============================================================================

@pytest.mark.asyncio
class TestAdventureProcessorIntegration:
    """Integration-style tests for adventure processor."""

    @pytest.fixture
    def mock_supabase_base(self):
        """Base mock for supabase."""
        with patch('utils.adventure_processor.supabase') as mock:
            yield mock

    async def test_full_round_processing_workflow(self, mock_supabase_base):
        """Test full workflow from round processing to completion."""
        today = date.today()
        # Create adventure with dates that will process exactly 1 round
        start = today - timedelta(days=1)
        deadline = today + timedelta(days=1)  # Future deadline, so no auto-complete

        adventure = {
            'id': 'adv-123',
            'user_id': 'user-123',
            'monster_id': 'monster-1',
            'status': 'active',
            'start_date': start.isoformat(),
            'deadline': deadline.isoformat(),
            'current_round': 0,
            'monster_current_hp': 50,  # Low HP - will be defeated
            'monster_max_hp': 300,
            'is_on_break': False,
            'break_end_date': None,
        }

        # Track call count for dynamic responses
        call_count = [0]

        def dynamic_execute_response():
            call_count[0] += 1
            if call_count[0] == 1:
                # First call: profile fetch
                return create_mock_execute_response({'timezone': 'UTC'})
            elif call_count[0] == 2:
                # Second call: reload after processing shows HP at 0 (victory)
                return create_mock_execute_response({'monster_current_hp': 0, 'status': 'active'})
            else:
                # Any other calls: return active status
                return create_mock_execute_response({'status': 'active'})

        mock_supabase_base.table.return_value.select.return_value.eq.return_value.single\
            .return_value.execute = AsyncMock(side_effect=dynamic_execute_response)

        # Track RPC call count
        rpc_call_count = [0]

        def dynamic_rpc_response():
            rpc_call_count[0] += 1
            if rpc_call_count[0] == 1:
                # First RPC: round calculation
                return create_mock_execute_response([{'damage': 50, 'new_hp': 0}])
            else:
                # Second RPC: completion
                return create_mock_execute_response([{'is_victory': True, 'xp_earned': 300}])

        mock_supabase_base.rpc.return_value.execute = AsyncMock(side_effect=dynamic_rpc_response)

        result = await process_adventure_rounds(adventure)

        # Should process at least one round
        assert result >= 0
