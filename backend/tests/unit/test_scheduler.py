"""
Unit tests for the background scheduler.

Tests hourly job processing for both battles and adventures.
"""
from unittest.mock import Mock, patch, call
import pytest


class TestProcessActiveBattles:
    """Test battle processing job."""

    def test_logs_start_of_battle_check(self):
        """Test that battle processing logs start message."""
        with patch('scheduler.logger') as mock_logger:
            with patch('scheduler.supabase') as mock_supabase:
                # Mock no active battles
                mock_res = Mock()
                mock_res.data = []
                mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_res

                from scheduler import process_active_battles

                process_active_battles()

                mock_logger.info.assert_any_call("Running hourly battle check")

    def test_fetches_active_battles(self):
        """Test that active battles are fetched from database."""
        with patch('scheduler.logger'):
            with patch('scheduler.supabase') as mock_supabase:
                mock_res = Mock()
                mock_res.data = []
                mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_res

                from scheduler import process_active_battles

                process_active_battles()

                # Verify battles table was queried
                mock_supabase.table.assert_called_with("battles")
                # Verify status filter was applied
                mock_supabase.table.return_value.select.return_value.eq.assert_called_with("status", "active")

    def test_processes_each_battle(self):
        """Test that each active battle is processed."""
        with patch('scheduler.logger') as mock_logger:
            with patch('scheduler.supabase') as mock_supabase:
                with patch('scheduler.process_battle_rounds') as mock_process:
                    # Mock two active battles
                    mock_res = Mock()
                    mock_res.data = [
                        {'id': 'battle-1', 'user1_id': 'user-1', 'user2_id': 'user-2'},
                        {'id': 'battle-2', 'user1_id': 'user-3', 'user2_id': 'user-4'}
                    ]
                    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_res
                    mock_process.return_value = 1  # Each battle processes 1 round

                    from scheduler import process_active_battles

                    process_active_battles()

                    # Verify both battles were processed
                    assert mock_process.call_count == 2

    def test_logs_rounds_processed(self):
        """Test that number of rounds processed is logged."""
        with patch('scheduler.logger') as mock_logger:
            with patch('scheduler.supabase') as mock_supabase:
                with patch('scheduler.process_battle_rounds') as mock_process:
                    mock_res = Mock()
                    mock_res.data = [{'id': 'battle-1', 'user1_id': 'user-1', 'user2_id': 'user-2'}]
                    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_res
                    mock_process.return_value = 2

                    from scheduler import process_active_battles

                    process_active_battles()

                    mock_logger.info.assert_any_call("Hourly check complete. Processed 2 round(s)")

    def test_handles_database_error_gracefully(self):
        """Test that database errors are caught and logged."""
        with patch('scheduler.logger') as mock_logger:
            with patch('scheduler.supabase') as mock_supabase:
                # Mock database error
                mock_supabase.table.return_value.select.return_value.eq.return_value.execute.side_effect = Exception("DB Error")

                from scheduler import process_active_battles

                # Should not raise exception
                process_active_battles()

                # Error should be logged
                mock_logger.error.assert_called()

    def test_handles_processing_error_for_single_battle(self):
        """Test that error processing one battle doesn't stop others."""
        with patch('scheduler.logger') as mock_logger:
            with patch('scheduler.supabase') as mock_supabase:
                with patch('scheduler.process_battle_rounds') as mock_process:
                    mock_res = Mock()
                    mock_res.data = [
                        {'id': 'battle-1', 'user1_id': 'user-1', 'user2_id': 'user-2'},
                        {'id': 'battle-2', 'user1_id': 'user-3', 'user2_id': 'user-4'}
                    ]
                    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_res

                    # First battle fails, second succeeds
                    mock_process.side_effect = [Exception("Battle error"), 1]

                    from scheduler import process_active_battles

                    # Should not raise exception
                    process_active_battles()

                    # Both should be attempted
                    assert mock_process.call_count == 2
                    # Error should be logged
                    mock_logger.error.assert_called()


class TestProcessActiveAdventures:
    """Test adventure processing job."""

    def test_logs_start_of_adventure_check(self):
        """Test that adventure processing logs start message."""
        with patch('scheduler.logger') as mock_logger:
            with patch('scheduler.supabase') as mock_supabase:
                mock_res = Mock()
                mock_res.data = []
                mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_res

                from scheduler import process_active_adventures

                process_active_adventures()

                mock_logger.info.assert_any_call("Running hourly adventure check")

    def test_fetches_active_adventures(self):
        """Test that active adventures are fetched from database."""
        with patch('scheduler.logger'):
            with patch('scheduler.supabase') as mock_supabase:
                mock_res = Mock()
                mock_res.data = []
                mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_res

                from scheduler import process_active_adventures

                process_active_adventures()

                # Verify adventures table was queried
                mock_supabase.table.assert_called_with("adventures")
                # Verify status filter was applied
                mock_supabase.table.return_value.select.return_value.eq.assert_called_with("status", "active")

    def test_includes_monster_data_in_query(self):
        """Test that adventure query includes monster data."""
        with patch('scheduler.logger'):
            with patch('scheduler.supabase') as mock_supabase:
                mock_res = Mock()
                mock_res.data = []
                mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_res

                from scheduler import process_active_adventures

                process_active_adventures()

                # Verify select includes monster relation
                mock_supabase.table.return_value.select.assert_called_with("*, monster:monsters(*)")

    def test_processes_each_adventure(self):
        """Test that each active adventure is processed."""
        with patch('scheduler.logger'):
            with patch('scheduler.supabase') as mock_supabase:
                with patch('scheduler.process_adventure_rounds') as mock_process:
                    mock_res = Mock()
                    mock_res.data = [
                        {'id': 'adventure-1', 'user_id': 'user-1', 'monster': {'id': 'monster-1'}},
                        {'id': 'adventure-2', 'user_id': 'user-2', 'monster': {'id': 'monster-2'}}
                    ]
                    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_res
                    mock_process.return_value = 1

                    from scheduler import process_active_adventures

                    process_active_adventures()

                    assert mock_process.call_count == 2

    def test_logs_rounds_processed(self):
        """Test that number of adventure rounds processed is logged."""
        with patch('scheduler.logger') as mock_logger:
            with patch('scheduler.supabase') as mock_supabase:
                with patch('scheduler.process_adventure_rounds') as mock_process:
                    mock_res = Mock()
                    mock_res.data = [{'id': 'adventure-1', 'user_id': 'user-1', 'monster': {'id': 'monster-1'}}]
                    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_res
                    mock_process.return_value = 3

                    from scheduler import process_active_adventures

                    process_active_adventures()

                    mock_logger.info.assert_any_call("Adventure check complete. Processed 3 round(s)")

    def test_handles_database_error_gracefully(self):
        """Test that database errors are caught and logged."""
        with patch('scheduler.logger') as mock_logger:
            with patch('scheduler.supabase') as mock_supabase:
                mock_supabase.table.return_value.select.return_value.eq.return_value.execute.side_effect = Exception("DB Error")

                from scheduler import process_active_adventures

                process_active_adventures()

                mock_logger.error.assert_called()

    def test_handles_processing_error_for_single_adventure(self):
        """Test that error processing one adventure doesn't stop others."""
        with patch('scheduler.logger') as mock_logger:
            with patch('scheduler.supabase') as mock_supabase:
                with patch('scheduler.process_adventure_rounds') as mock_process:
                    mock_res = Mock()
                    mock_res.data = [
                        {'id': 'adventure-1', 'user_id': 'user-1', 'monster': {'id': 'monster-1'}},
                        {'id': 'adventure-2', 'user_id': 'user-2', 'monster': {'id': 'monster-2'}}
                    ]
                    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_res

                    mock_process.side_effect = [Exception("Adventure error"), 1]

                    from scheduler import process_active_adventures

                    process_active_adventures()

                    assert mock_process.call_count == 2
                    mock_logger.error.assert_called()


class TestStartScheduler:
    """Test scheduler startup."""

    def test_adds_battle_job(self):
        """Test that battle processing job is added."""
        with patch('scheduler.scheduler') as mock_scheduler:
            from scheduler import start_scheduler, process_active_battles

            start_scheduler()

            # Get all add_job calls
            calls = mock_scheduler.add_job.call_args_list

            # Check that battle job was added
            battle_call_found = False
            for call_item in calls:
                kwargs = call_item.kwargs if call_item.kwargs else {}
                if 'id' in kwargs and kwargs['id'] == 'process_battles':
                    battle_call_found = True
                    # Verify the other parameters
                    assert kwargs.get('trigger') == 'cron'
                    assert kwargs.get('minute') == 0
                    assert kwargs.get('replace_existing') is True
                    # First positional arg should be the function
                    if call_item[0]:  # args exist
                        assert call_item[0][0] == process_active_battles
                    break

            assert battle_call_found, "Battle job not found in scheduler calls"

    def test_adds_adventure_job(self):
        """Test that adventure processing job is added."""
        with patch('scheduler.scheduler') as mock_scheduler:
            from scheduler import start_scheduler, process_active_adventures

            start_scheduler()

            # Get all add_job calls
            calls = mock_scheduler.add_job.call_args_list

            # Check that adventure job was added
            adventure_call_found = False
            for call_item in calls:
                kwargs = call_item.kwargs if call_item.kwargs else {}
                if 'id' in kwargs and kwargs['id'] == 'process_adventures':
                    adventure_call_found = True
                    # Verify the other parameters
                    assert kwargs.get('trigger') == 'cron'
                    assert kwargs.get('minute') == 0
                    assert kwargs.get('replace_existing') is True
                    # First positional arg should be the function
                    if call_item[0]:  # args exist
                        assert call_item[0][0] == process_active_adventures
                    break

            assert adventure_call_found, "Adventure job not found in scheduler calls"

    def test_starts_scheduler(self):
        """Test that scheduler is started."""
        with patch('scheduler.scheduler') as mock_scheduler:
            from scheduler import start_scheduler

            start_scheduler()

            mock_scheduler.start.assert_called_once()

    def test_logs_startup_message(self):
        """Test that startup is logged."""
        with patch('scheduler.scheduler'):
            with patch('scheduler.logger') as mock_logger:
                from scheduler import start_scheduler

                start_scheduler()

                mock_logger.info.assert_called_with(
                    "Background scheduler started (hourly battle + adventure processing)"
                )


class TestShutdownScheduler:
    """Test scheduler shutdown."""

    def test_shutdowns_scheduler(self):
        """Test that scheduler is shut down gracefully."""
        with patch('scheduler.scheduler') as mock_scheduler:
            from scheduler import shutdown_scheduler

            shutdown_scheduler()

            mock_scheduler.shutdown.assert_called_once()

    def test_logs_shutdown_message(self):
        """Test that shutdown is logged."""
        with patch('scheduler.scheduler'):
            with patch('scheduler.logger') as mock_logger:
                from scheduler import shutdown_scheduler

                shutdown_scheduler()

                mock_logger.info.assert_called_with("Background scheduler stopped")
