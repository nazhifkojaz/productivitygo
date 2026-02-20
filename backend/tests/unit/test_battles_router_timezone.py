"""
Unit tests for timezone handling in battles router.

Tests that verify get_current_battle passes the user's local date
(not UTC date) when fetching rival tasks.
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock, call
from datetime import date, timedelta


@pytest.mark.asyncio
class TestTimezoneInGetCurrentBattle:
    """Test that user's local date is used for rival task fetching."""

    async def test_user_local_date_used_for_rival_tasks_not_utc(self):
        """
        CRITICAL TEST: Verify get_current_battle uses user's local date,
        not UTC date, when fetching rival tasks.

        Bug: Line 124 in battles.py uses date.today() which returns UTC date.
        Fix: Should use user_today which is the user's timezone-aware local date.

        Scenario:
        - User in Asia/Tokyo (UTC+9)
        - Current UTC time: 2026-02-18 18:00 (6 PM)
        - User's local time: 2026-02-19 03:00 (3 AM next day)
        - UTC date: 2026-02-18
        - User's local date: 2026-02-19

        Expected Behavior:
        - get_local_date('Asia/Tokyo') should return 2026-02-19
        - fetch_rival_tasks_for_today should be called with '2026-02-19' (user's local date)
        - NOT with '2026-02-18' (UTC date)

        This test will FAIL before the fix and PASS after the fix.
        """
        # Setup: Mock user with Asia/Tokyo timezone
        mock_user = Mock(id="user-123", email="tokyo@example.com")

        sample_battle = {
            'id': 'battle-123',
            'user1_id': 'user-123',
            'user2_id': 'rival-456',
            'start_date': '2026-02-15',
            'end_date': '2026-02-20',
            'duration': 5,
            'current_round': 0,
            'status': 'active',
            'user1': {
                'timezone': 'Asia/Tokyo',
                'username': 'TokyoPlayer',
                'level': 5,
                'battle_win_count': 3,
                'battle_count': 10,
                'total_xp_earned': 2500,
                'completed_tasks': 45
            },
            'user2': {
                'timezone': 'UTC',
                'username': 'Rival',
                'level': 3,
                'battle_win_count': 1,
                'battle_count': 5,
                'total_xp_earned': 1200,
                'completed_tasks': 25
            }
        }

        with patch('services.battle_query_service.supabase') as mock_supabase:
            # Mock process_battle_rounds to return 0
            async def mock_process(*args, **kwargs):
                return 0

            with patch('utils.battle_processor.process_battle_rounds', side_effect=mock_process):
                # Track what date string is passed to fetch_rival_tasks_for_today
                captured_date_strings = []

                async def mock_fetch_rival_tasks(rival_id, today_str):
                    """Mock that captures the date string passed"""
                    captured_date_strings.append(today_str)
                    # Return some dummy task data
                    return (3, 2)  # 3 total tasks, 2 completed

                # Patch the service method to capture calls
                with patch('services.battle_query_service.BattleQueryService.fetch_rival_tasks_for_today',
                          side_effect=mock_fetch_rival_tasks):

                    # Mock battles query
                    mock_battle_execute = AsyncMock(return_value=Mock(
                        data=[sample_battle]
                    ))

                    # Mock daily_entries query (returns empty for rounds played)
                    mock_entries_execute = AsyncMock(return_value=Mock(data=[]))

                    # Mock reload query
                    mock_reload_execute = AsyncMock(return_value=Mock(data=None))

                    def mock_table(table_name):
                        if table_name == "battles":
                            mock_obj = Mock()
                            mock_obj.select.return_value.or_.return_value.eq.return_value.execute = mock_battle_execute
                            mock_obj.select.return_value.eq.return_value.single.return_value.execute = mock_reload_execute
                            mock_obj.update.return_value.eq.return_value.execute = AsyncMock(return_value=Mock())
                            return mock_obj
                        elif table_name == "daily_entries":
                            mock_obj = Mock()
                            mock_obj.select.return_value.eq.return_value.eq.return_value.execute = mock_entries_execute
                            return mock_obj
                        return Mock()

                    mock_supabase.table.side_effect = mock_table
                    mock_supabase.rpc.return_value.execute = AsyncMock(return_value=Mock(data=None))

                    # Mock get_local_date to simulate Tokyo being ahead of UTC
                    # UTC: 2026-02-18, Tokyo: 2026-02-19 (already next day)
                    tokyo_date = date(2026, 2, 19)
                    with patch('routers.battles.get_local_date', return_value=tokyo_date):
                        # Mock date.today() to return UTC date (this is what causes the bug)
                        with patch('routers.battles.date') as mock_date:
                            mock_date.today.return_value = date(2026, 2, 18)  # UTC date
                            mock_date.fromisoformat = date.fromisoformat

                            from routers.battles import get_current_battle
                            result = await get_current_battle(mock_user)

                            # Verify the result was returned
                            assert result is not None
                            assert 'rival' in result

                            # CRITICAL ASSERTION:
                            # The captured date should be the user's LOCAL date (2026-02-19)
                            # NOT the UTC date (2026-02-18)
                            #
                            # Before fix: captured_date_strings = ['2026-02-18'] (UTC date) - TEST FAILS
                            # After fix: captured_date_strings = ['2026-02-19'] (user's local date) - TEST PASSES
                            assert len(captured_date_strings) == 1, \
                                f"Expected fetch_rival_tasks_for_today to be called once, got {len(captured_date_strings)} calls"

                            actual_date = captured_date_strings[0]
                            expected_date = '2026-02-19'  # User's local date (Tokyo)

                            assert actual_date == expected_date, (
                                f"Expected rival tasks to be fetched for user's local date "
                                f"'{expected_date}' (Tokyo time), but got '{actual_date}' (UTC date). "
                                f"This indicates the bug at line 124 of battles.py: "
                                f"using date.today() instead of user_today."
                            )

                            # Verify the rival data reflects the mocked fetch result
                            assert result['rival']['tasks_total'] == 3
                            assert result['rival']['tasks_completed'] == 2

    async def test_utc_plus_5_user_sees_correct_rival_progress(self):
        """
        Test edge case: User in UTC+5:30 (India) sees correct rival progress.

        Scenario:
        - User in Asia/Kolkata (UTC+5:30)
        - UTC time: 2026-02-19 20:00
        - User's local time: 2026-02-20 01:30 (next day)
        - Expected: Fetch rival tasks for 2026-02-20 (user's local date)
        """
        mock_user = Mock(id="user-in", email="india@example.com")

        sample_battle = {
            'id': 'battle-456',
            'user1_id': 'user-in',
            'user2_id': 'rival-us',
            'start_date': '2026-02-15',
            'end_date': '2026-02-22',
            'duration': 7,
            'current_round': 0,
            'status': 'active',
            'user1': {
                'timezone': 'Asia/Kolkata',
                'username': 'IndiaPlayer',
                'level': 7,
                'battle_win_count': 5,
                'battle_count': 12,
                'total_xp_earned': 3500,
                'completed_tasks': 60
            },
            'user2': {
                'timezone': 'America/New_York',
                'username': 'USPlayer',
                'level': 6,
                'battle_win_count': 4,
                'battle_count': 10,
                'total_xp_earned': 2800,
                'completed_tasks': 50
            }
        }

        with patch('services.battle_query_service.supabase') as mock_supabase:
            async def mock_process(*args, **kwargs):
                return 0

            with patch('utils.battle_processor.process_battle_rounds', side_effect=mock_process):
                captured_dates = []

                async def mock_fetch_rival_tasks(rival_id, today_str):
                    captured_dates.append(today_str)
                    return (5, 3)

                with patch('services.battle_query_service.BattleQueryService.fetch_rival_tasks_for_today',
                          side_effect=mock_fetch_rival_tasks):

                    mock_battle_execute = AsyncMock(return_value=Mock(data=[sample_battle]))
                    mock_entries_execute = AsyncMock(return_value=Mock(data=[]))
                    mock_reload_execute = AsyncMock(return_value=Mock(data=None))

                    def mock_table(table_name):
                        if table_name == "battles":
                            m = Mock()
                            m.select.return_value.or_.return_value.eq.return_value.execute = mock_battle_execute
                            m.select.return_value.eq.return_value.single.return_value.execute = mock_reload_execute
                            m.update.return_value.eq.return_value.execute = AsyncMock(return_value=Mock())
                            return m
                        elif table_name == "daily_entries":
                            m = Mock()
                            m.select.return_value.eq.return_value.eq.return_value.execute = mock_entries_execute
                            return m
                        return Mock()

                    mock_supabase.table.side_effect = mock_table
                    mock_supabase.rpc.return_value.execute = AsyncMock(return_value=Mock(data=None))

                    # India is ahead: UTC 2026-02-19, India 2026-02-20
                    with patch('routers.battles.get_local_date', return_value=date(2026, 2, 20)):
                        with patch('routers.battles.date') as mock_date:
                            mock_date.today.return_value = date(2026, 2, 19)  # UTC date behind
                            mock_date.fromisoformat = date.fromisoformat

                            from routers.battles import get_current_battle
                            result = await get_current_battle(mock_user)

                            assert result is not None
                            assert len(captured_dates) == 1
                            assert captured_dates[0] == '2026-02-20', (
                                f"India user (UTC+5:30) should see rival tasks for their local date "
                                f"'2026-02-20', not UTC date '{captured_dates[0]}'"
                            )

    async def test_utc_minus_user_sees_correct_rival_progress(self):
        """
        Test that UTC- users (unaffected by bug) still work correctly after fix.

        Scenario:
        - User in America/Los_Angeles (UTC-8)
        - UTC time: 2026-02-19 10:00
        - User's local time: 2026-02-19 02:00 (same day)
        - Expected: Fetch rival tasks for 2026-02-19 (same for both UTC and local)
        """
        mock_user = Mock(id="user-la", email="la@example.com")

        sample_battle = {
            'id': 'battle-789',
            'user1_id': 'user-la',
            'user2_id': 'rival-ny',
            'start_date': '2026-02-15',
            'end_date': '2026-02-20',
            'duration': 5,
            'current_round': 0,
            'status': 'active',
            'user1': {
                'timezone': 'America/Los_Angeles',
                'username': 'LAPlayer',
                'level': 4,
                'battle_win_count': 2,
                'battle_count': 8,
                'total_xp_earned': 1800,
                'completed_tasks': 35
            },
            'user2': {
                'timezone': 'UTC',
                'username': 'NYPlayer',
                'level': 5,
                'battle_win_count': 3,
                'battle_count': 9,
                'total_xp_earned': 2200,
                'completed_tasks': 42
            }
        }

        with patch('services.battle_query_service.supabase') as mock_supabase:
            async def mock_process(*args, **kwargs):
                return 0

            with patch('utils.battle_processor.process_battle_rounds', side_effect=mock_process):
                captured_dates = []

                async def mock_fetch_rival_tasks(rival_id, today_str):
                    captured_dates.append(today_str)
                    return (2, 2)

                with patch('services.battle_query_service.BattleQueryService.fetch_rival_tasks_for_today',
                          side_effect=mock_fetch_rival_tasks):

                    mock_battle_execute = AsyncMock(return_value=Mock(data=[sample_battle]))
                    mock_entries_execute = AsyncMock(return_value=Mock(data=[]))
                    mock_reload_execute = AsyncMock(return_value=Mock(data=None))

                    def mock_table(table_name):
                        if table_name == "battles":
                            m = Mock()
                            m.select.return_value.or_.return_value.eq.return_value.execute = mock_battle_execute
                            m.select.return_value.eq.return_value.single.return_value.execute = mock_reload_execute
                            m.update.return_value.eq.return_value.execute = AsyncMock(return_value=Mock())
                            return m
                        elif table_name == "daily_entries":
                            m = Mock()
                            m.select.return_value.eq.return_value.eq.return_value.execute = mock_entries_execute
                            return m
                        return Mock()

                    mock_supabase.table.side_effect = mock_table
                    mock_supabase.rpc.return_value.execute = AsyncMock(return_value=Mock(data=None))

                    # LA is behind UTC: same day for both
                    with patch('routers.battles.get_local_date', return_value=date(2026, 2, 19)):
                        with patch('routers.battles.date') as mock_date:
                            mock_date.today.return_value = date(2026, 2, 19)
                            mock_date.fromisoformat = date.fromisoformat

                            from routers.battles import get_current_battle
                            result = await get_current_battle(mock_user)

                            assert result is not None
                            assert len(captured_dates) == 1
                            # When UTC and local date are the same, both should work
                            assert captured_dates[0] == '2026-02-19'
                            assert result['rival']['tasks_total'] == 2
                            assert result['rival']['tasks_completed'] == 2

    async def test_no_rival_entry_returns_zero_tasks(self):
        """
        Test that when rival has no entry for user's local date, returns (0, 0).

        This is correct behavior - if rival hasn't planned tasks for the user's
        local date yet (e.g., rival is in UTC-5 and it's still yesterday for them),
        we should show 0/0 tasks rather than fetching yesterday's data.
        """
        mock_user = Mock(id="user-tokyo", email="tokyo@example.com")

        sample_battle = {
            'id': 'battle-999',
            'user1_id': 'user-tokyo',
            'user2_id': 'rival-ny',
            'start_date': '2026-02-15',
            'end_date': '2026-02-20',
            'duration': 5,
            'current_round': 0,
            'status': 'active',
            'user1': {
                'timezone': 'Asia/Tokyo',
                'username': 'TokyoPlayer',
                'level': 5,
                'battle_win_count': 3,
                'battle_count': 10,
                'total_xp_earned': 2500,
                'completed_tasks': 45
            },
            'user2': {
                'timezone': 'America/New_York',
                'username': 'NYPlayer',
                'level': 4,
                'battle_win_count': 2,
                'battle_count': 8,
                'total_xp_earned': 1800,
                'completed_tasks': 35
            }
        }

        with patch('services.battle_query_service.supabase') as mock_supabase:
            async def mock_process(*args, **kwargs):
                return 0

            with patch('utils.battle_processor.process_battle_rounds', side_effect=mock_process):
                captured_dates = []

                async def mock_fetch_rival_tasks(rival_id, today_str):
                    captured_dates.append(today_str)
                    # No entry found for this date
                    return (0, 0)

                with patch('services.battle_query_service.BattleQueryService.fetch_rival_tasks_for_today',
                          side_effect=mock_fetch_rival_tasks):

                    mock_battle_execute = AsyncMock(return_value=Mock(data=[sample_battle]))
                    mock_entries_execute = AsyncMock(return_value=Mock(data=[]))
                    mock_reload_execute = AsyncMock(return_value=Mock(data=None))

                    def mock_table(table_name):
                        if table_name == "battles":
                            m = Mock()
                            m.select.return_value.or_.return_value.eq.return_value.execute = mock_battle_execute
                            m.select.return_value.eq.return_value.single.return_value.execute = mock_reload_execute
                            m.update.return_value.eq.return_value.execute = AsyncMock(return_value=Mock())
                            return m
                        elif table_name == "daily_entries":
                            m = Mock()
                            m.select.return_value.eq.return_value.eq.return_value.execute = mock_entries_execute
                            return m
                        return Mock()

                    mock_supabase.table.side_effect = mock_table
                    mock_supabase.rpc.return_value.execute = AsyncMock(return_value=Mock(data=None))

                    # Tokyo is ahead: queries for Feb 20, but NY rival hasn't created that entry yet
                    with patch('routers.battles.get_local_date', return_value=date(2026, 2, 20)):
                        with patch('routers.battles.date') as mock_date:
                            mock_date.today.return_value = date(2026, 2, 19)  # UTC behind
                            mock_date.fromisoformat = date.fromisoformat

                            from routers.battles import get_current_battle
                            result = await get_current_battle(mock_user)

                            assert result is not None
                            # Should query for Tokyo's local date (Feb 20), even though rival has no entry
                            assert len(captured_dates) == 1
                            assert captured_dates[0] == '2026-02-20'
                            # Rival should show 0/0 tasks because no entry exists for Feb 20
                            assert result['rival']['tasks_total'] == 0
                            assert result['rival']['tasks_completed'] == 0
