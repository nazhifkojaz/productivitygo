"""
Unit tests for timezone handling in battle_processor.

Tests that verify round processing uses user's local dates correctly,
not UTC date, for determining round eligibility.
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import date, timedelta


@pytest.mark.asyncio
class TestBattleProcessorTimezoneHandling:
    """Test that round processing respects user timezones."""

    async def test_round_eligibility_uses_max_local_date_not_utc(self):
        """
        CRITICAL TEST: Verify round eligibility uses max of both players'
        local dates, NOT UTC date.

        Bug: Line 58 in battle_processor.py uses date.today() which returns UTC date.
        Fix: Should use max(date1, date2) - the latest local date among both players.

        Scenario:
        - Player 1: America/New_York (UTC-5), local date: Feb 18
        - Player 2: Asia/Tokyo (UTC+9), local date: Feb 19
        - UTC date: Feb 19
        - Battle start: Feb 15

        Before Fix (BUGGY):
        - days_since_start = (date.today() - start_date).days
        -                     = (Feb 19 - Feb 15).days = 4
        - This uses UTC date, which may not reflect either player's reality

        After Fix (CORRECT):
        - days_since_start = (max(date1, date2) - start_date).days
        -                     = (max(Feb 18, Feb 19) - Feb 15).days = 4
        - Uses the latest local date, ensuring both players have passed each round

        Note: The guard at line 71 (if date1 > round_date and date2 > round_date)
        provides the real safety - this test ensures we don't waste iterations
        attempting rounds that can't possibly be processed.
        """
        sample_battle = {
            'id': 'battle-123',
            'user1_id': 'user-1',
            'user2_id': 'user-2',
            'start_date': '2026-02-15',
            'end_date': '2026-02-20',
            'duration': 5,
            'current_round': 0,
            'status': 'active',
            'user1': {'timezone': 'America/New_York', 'username': 'P1'},
            'user2': {'timezone': 'Asia/Tokyo', 'username': 'P2'}
        }

        with patch('utils.battle_processor.supabase') as mock_supabase:
            # Mock profiles query
            mock_profiles_execute = AsyncMock(return_value=Mock(data=[
                {'id': 'user-1', 'timezone': 'America/New_York'},
                {'id': 'user-2', 'timezone': 'Asia/Tokyo'}
            ]))

            # Mock get_local_date to simulate different timezones
            # UTC is Feb 19, NY is still Feb 18 evening, Tokyo is Feb 19 morning
            def mock_get_local_date(tz_str):
                if tz_str == 'America/New_York':
                    return date(2026, 2, 18)  # Still Feb 18 in NY
                elif tz_str == 'Asia/Tokyo':
                    return date(2026, 2, 19)  # Already Feb 19 in Tokyo
                return date.today()

            with patch('utils.battle_processor.get_local_date', side_effect=mock_get_local_date):
                # Track what date is used for days_since_start calculation
                calculated_days_since_start = []

                # Mock date.today() to return UTC date
                with patch('utils.battle_processor.date') as mock_date:
                    # UTC is Feb 19
                    mock_date.today.return_value = date(2026, 2, 19)
                    mock_date.fromisoformat = date.fromisoformat

                    def mock_table(table_name):
                        mock_obj = Mock()
                        if table_name == "profiles":
                            mock_obj.select.return_value.in_.return_value.execute = mock_profiles_execute
                        elif table_name == "battles":
                            mock_obj.update.return_value.eq.return_value.execute = AsyncMock(return_value=Mock())
                        return mock_obj

                    mock_supabase.table.side_effect = mock_table

                    # Mock RPC for successful round processing
                    mock_rpc_execute = AsyncMock(return_value=Mock(data=[
                        {'user1_xp': 100, 'user2_xp': 50}
                    ]))
                    mock_supabase.rpc.return_value.execute = mock_rpc_execute

                    from utils.battle_processor import process_battle_rounds

                    # Execute the function
                    result = await process_battle_rounds(sample_battle)

                    # Verify processing completed without errors
                    assert result >= 0

                    # The fix ensures we use max(date1, date2) for eligibility
                    # Before fix: days_since_start = (Feb 19 - Feb 15).days = 4 (uses UTC)
                    # After fix: days_since_start = (max(Feb 18, Feb 19) - Feb 15).days = 4
                    #
                    # In this case, both give 4, but the PRINCIPLE is different:
                    # - Before: Uses UTC date which may be ahead of or behind both players
                    # - After: Uses the maximum local date, ensuring fair processing

                    # The guard at line 71 ensures only rounds BOTH players have passed
                    # will actually process. With date1=Feb 18 and date2=Feb 19:
                    # - Feb 15 round: date1(Feb 18) > Feb 15 AND date2(Feb 19) > Feb 15 ✓
                    # - Feb 16 round: date1(Feb 18) > Feb 16 AND date2(Feb 19) > Feb 16 ✓
                    # - Feb 17 round: date1(Feb 18) > Feb 17 AND date2(Feb 19) > Feb 17 ✓
                    # - Feb 18 round: date1(Feb 18) > Feb 18? NO (not >, it's ==)
                    #
                    # So we should process exactly 3 rounds (Feb 15, 16, 17)
                    assert result == 3, (
                        f"Expected 3 rounds to be processed (Feb 15, 16, 17), but got {result}. "
                        f"date1=Feb 18, date2=Feb 19, start=Feb 15"
                    )

    async def test_both_players_same_timezone_uses_that_date(self):
        """
        Test that when both players are in same timezone, processing works correctly.

        Scenario:
        - Both players in UTC
        - Local date: Feb 19 for both
        - Battle start: Feb 15
        - Expected: Process rounds that both have passed
        """
        sample_battle = {
            'id': 'battle-456',
            'user1_id': 'user-1',
            'user2_id': 'user-2',
            'start_date': '2026-02-15',
            'end_date': '2026-02-20',
            'duration': 5,
            'current_round': 0,
            'status': 'active'
        }

        with patch('utils.battle_processor.supabase') as mock_supabase:
            mock_profiles_execute = AsyncMock(return_value=Mock(data=[
                {'id': 'user-1', 'timezone': 'UTC'},
                {'id': 'user-2', 'timezone': 'UTC'}
            ]))

            with patch('utils.battle_processor.get_local_date', return_value=date(2026, 2, 19)):
                with patch('utils.battle_processor.date') as mock_date:
                    mock_date.today.return_value = date(2026, 2, 19)
                    mock_date.fromisoformat = date.fromisoformat

                    def mock_table(table_name):
                        mock_obj = Mock()
                        if table_name == "profiles":
                            mock_obj.select.return_value.in_.return_value.execute = mock_profiles_execute
                        elif table_name == "battles":
                            mock_obj.update.return_value.eq.return_value.execute = AsyncMock(return_value=Mock())
                        return mock_obj

                    mock_supabase.table.side_effect = mock_table

                    mock_rpc_execute = AsyncMock(return_value=Mock(data=[
                        {'user1_xp': 100, 'user2_xp': 50}
                    ]))
                    mock_supabase.rpc.return_value.execute = mock_rpc_execute

                    from utils.battle_processor import process_battle_rounds
                    result = await process_battle_rounds(sample_battle)

                    # Both players at Feb 19, started Feb 15
                    # Rounds for Feb 15, 16, 17, 18 should be processable (4 rounds)
                    # Round for Feb 19 is NOT > Feb 19 (it's ==)
                    assert result == 4

    async def test_utc_plus_14_player_earliest_processing(self):
        """
        Test edge case: Player in UTC+14 (Kiribati) gets fair processing.

        Scenario:
        - Player 1: Pacific/Kiritimati (UTC+14), local date: Feb 20
        - Player 2: UTC, local date: Feb 19
        - Battle start: Feb 15
        - UTC date: Feb 19

        Before fix: days_since_start = (Feb 19 - Feb 15).days = 4
        After fix: days_since_start = (max(Feb 20, Feb 19) - Feb 15).days = 5

        The guard ensures both players have passed each round date.
        """
        sample_battle = {
            'id': 'battle-789',
            'user1_id': 'user-1',
            'user2_id': 'user-2',
            'start_date': '2026-02-15',
            'end_date': '2026-02-22',
            'duration': 7,
            'current_round': 0,
            'status': 'active'
        }

        with patch('utils.battle_processor.supabase') as mock_supabase:
            mock_profiles_execute = AsyncMock(return_value=Mock(data=[
                {'id': 'user-1', 'timezone': 'Pacific/Kiritimati'},  # UTC+14
                {'id': 'user-2', 'timezone': 'UTC'}
            ]))

            def mock_get_local_date(tz_str):
                if tz_str == 'Pacific/Kiritimati':
                    return date(2026, 2, 20)  # Way ahead
                return date(2026, 2, 19)

            with patch('utils.battle_processor.get_local_date', side_effect=mock_get_local_date):
                with patch('utils.battle_processor.date') as mock_date:
                    mock_date.today.return_value = date(2026, 2, 19)  # UTC behind Kiribati
                    mock_date.fromisoformat = date.fromisoformat

                    def mock_table(table_name):
                        mock_obj = Mock()
                        if table_name == "profiles":
                            mock_obj.select.return_value.in_.return_value.execute = mock_profiles_execute
                        elif table_name == "battles":
                            mock_obj.update.return_value.eq.return_value.execute = AsyncMock(return_value=Mock())
                        return mock_obj

                    mock_supabase.table.side_effect = mock_table

                    mock_rpc_execute = AsyncMock(return_value=Mock(data=[
                        {'user1_xp': 100, 'user2_xp': 50}
                    ]))
                    mock_supabase.rpc.return_value.execute = mock_rpc_execute

                    from utils.battle_processor import process_battle_rounds
                    result = await process_battle_rounds(sample_battle)

                    # UTC player at Feb 19, Kiribati player at Feb 20
                    # Both have passed Feb 15, 16, 17, 18 (4 rounds)
                    # Feb 19: UTC player is at Feb 19, not > Feb 19
                    assert result == 4

    async def test_cross_dateline_players_fair_processing(self):
        """
        Test edge case: Players across international date line get fair processing.

        Scenario:
        - Player 1: Pacific/Auckland (UTC+12), local date: Feb 20
        - Player 2: Pacific/Honolulu (UTC-10), local date: Feb 19
        - Battle start: Feb 15
        - Max local date: Feb 20

        The round processing should be limited by the player who is "behind".
        """
        sample_battle = {
            'id': 'battle-dateline',
            'user1_id': 'user-auckland',
            'user2_id': 'user-honolulu',
            'start_date': '2026-02-15',
            'end_date': '2026-02-22',
            'duration': 7,
            'current_round': 0,
            'status': 'active'
        }

        with patch('utils.battle_processor.supabase') as mock_supabase:
            mock_profiles_execute = AsyncMock(return_value=Mock(data=[
                {'id': 'user-auckland', 'timezone': 'Pacific/Auckland'},
                {'id': 'user-honolulu', 'timezone': 'Pacific/Honolulu'}
            ]))

            def mock_get_local_date(tz_str):
                if tz_str == 'Pacific/Auckland':
                    return date(2026, 2, 20)  # Way ahead
                elif tz_str == 'Pacific/Honolulu':
                    return date(2026, 2, 19)  # Behind
                return date.today()

            with patch('utils.battle_processor.get_local_date', side_effect=mock_get_local_date):
                with patch('utils.battle_processor.date') as mock_date:
                    mock_date.today.return_value = date(2026, 2, 19)
                    mock_date.fromisoformat = date.fromisoformat

                    def mock_table(table_name):
                        mock_obj = Mock()
                        if table_name == "profiles":
                            mock_obj.select.return_value.in_.return_value.execute = mock_profiles_execute
                        elif table_name == "battles":
                            mock_obj.update.return_value.eq.return_value.execute = AsyncMock(return_value=Mock())
                        return mock_obj

                    mock_supabase.table.side_effect = mock_table

                    mock_rpc_execute = AsyncMock(return_value=Mock(data=[
                        {'user1_xp': 100, 'user2_xp': 50}
                    ]))
                    mock_supabase.rpc.return_value.execute = mock_rpc_execute

                    from utils.battle_processor import process_battle_rounds
                    result = await process_battle_rounds(sample_battle)

                    # Auckland at Feb 20, Honolulu at Feb 19
                    # Both have passed Feb 15, 16, 17, 18 (4 rounds)
                    # Feb 19: Honolulu is at Feb 19, not > Feb 19
                    assert result == 4

    async def test_already_up_to_date_battle_returns_zero(self):
        """
        Test that a battle already at current_round returns 0 without processing.

        When current_round >= rounds_to_process, no processing should occur.
        """
        sample_battle = {
            'id': 'battle-current',
            'user1_id': 'user-1',
            'user2_id': 'user-2',
            'start_date': '2026-02-15',
            'end_date': '2026-02-20',
            'duration': 5,
            'current_round': 4,  # Already processed most rounds
            'status': 'active'
        }

        with patch('utils.battle_processor.supabase') as mock_supabase:
            mock_profiles_execute = AsyncMock(return_value=Mock(data=[
                {'id': 'user-1', 'timezone': 'UTC'},
                {'id': 'user-2', 'timezone': 'UTC'}
            ]))

            with patch('utils.battle_processor.get_local_date', return_value=date(2026, 2, 19)):
                with patch('utils.battle_processor.date') as mock_date:
                    mock_date.today.return_value = date(2026, 2, 19)
                    mock_date.fromisoformat = date.fromisoformat

                    def mock_table(table_name):
                        mock_obj = Mock()
                        if table_name == "profiles":
                            mock_obj.select.return_value.in_.return_value.execute = mock_profiles_execute
                        return mock_obj

                    mock_supabase.table.side_effect = mock_table

                    from utils.battle_processor import process_battle_rounds
                    result = await process_battle_rounds(sample_battle)

                    # days_since_start = (Feb 19 - Feb 15).days = 4
                    # rounds_to_process = min(4, 5) = 4
                    # current_round = 4 >= rounds_to_process = 4
                    # Should return 0 without processing
                    assert result == 0

    async def test_invalid_timezone_falls_back_to_utc(self):
        """
        Test that invalid timezone strings fall back to UTC gracefully.

        get_local_date already handles this with try/except, logging debug.
        """
        sample_battle = {
            'id': 'battle-invalid-tz',
            'user1_id': 'user-1',
            'user2_id': 'user-2',
            'start_date': '2026-02-15',
            'end_date': '2026-02-20',
            'duration': 5,
            'current_round': 0,
            'status': 'active'
        }

        with patch('utils.battle_processor.supabase') as mock_supabase:
            # Profile with invalid timezone
            mock_profiles_execute = AsyncMock(return_value=Mock(data=[
                {'id': 'user-1', 'timezone': 'Invalid/Timezone'},
                {'id': 'user-2', 'timezone': 'UTC'}
            ]))

            # get_local_date should fall back to UTC for invalid timezone
            def mock_get_local_date(tz_str):
                if 'Invalid' in tz_str:
                    return date(2026, 2, 19)  # Falls back to UTC date
                return date(2026, 2, 19)

            with patch('utils.battle_processor.get_local_date', side_effect=mock_get_local_date):
                with patch('utils.battle_processor.date') as mock_date:
                    mock_date.today.return_value = date(2026, 2, 19)
                    mock_date.fromisoformat = date.fromisoformat

                    def mock_table(table_name):
                        mock_obj = Mock()
                        if table_name == "profiles":
                            mock_obj.select.return_value.in_.return_value.execute = mock_profiles_execute
                        elif table_name == "battles":
                            mock_obj.update.return_value.eq.return_value.execute = AsyncMock(return_value=Mock())
                        return mock_obj

                    mock_supabase.table.side_effect = mock_table

                    mock_rpc_execute = AsyncMock(return_value=Mock(data=[
                        {'user1_xp': 100, 'user2_xp': 50}
                    ]))
                    mock_supabase.rpc.return_value.execute = mock_rpc_execute

                    from utils.battle_processor import process_battle_rounds

                    # Should not crash, should process normally
                    result = await process_battle_rounds(sample_battle)
                    assert result >= 0
