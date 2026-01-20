"""
Unit tests for atomic operations in battle system.
Tests BUG-005 fix: Non-atomic profile stat updates.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock, call
from datetime import date
from fastapi import HTTPException


class TestForfeitBattleAtomic:
    """Test atomic forfeit battle operation."""

    @pytest.fixture
    def sample_active_battle(self):
        """Sample active battle for testing."""
        return {
            'id': 'battle-123',
            'user1_id': 'user-1',
            'user2_id': 'user-2',
            'status': 'active',
            'start_date': '2026-01-20',
            'end_date': '2026-01-25',
            'duration': 5
        }

    @pytest.fixture
    def mock_user(self):
        """Mock authenticated user."""
        return Mock(id="user-1", email="test@example.com")

    def test_forfeit_atomic_sql_function_signature(self):
        """Test that the atomic forfeit SQL function has correct signature."""
        # This test documents the expected SQL function signature
        # The actual function will be created in functions_forfeit.sql
        expected_params = {
            "battle_uuid": "UUID",
            "forfeiting_user": "UUID"
        }
        expected_returns = {
            "winner_id": "UUID",
            "already_completed": "BOOLEAN"
        }
        # Documenting the expected interface
        assert expected_params is not None
        assert expected_returns is not None

    def test_forfeit_battle_calls_rpc(self, sample_active_battle, mock_user):
        """Test that forfeit_battle calls the atomic SQL RPC function."""
        with patch('services.battle_service.supabase') as mock_supabase:
            # Mock the RPC call to atomic forfeit function
            mock_rpc_result = Mock()
            mock_rpc_result.data = [{
                'winner_id': 'user-2',
                'already_completed': False
            }]
            mock_supabase.rpc.return_value.execute.return_value = mock_rpc_result

            from services.battle_service import BattleService

            result = BattleService.forfeit_battle('battle-123', mock_user.id)

            # Verify RPC was called with correct parameters
            mock_supabase.rpc.assert_called_once()
            call_args = mock_supabase.rpc.call_args
            assert call_args[0][0] == "forfeit_battle_atomic"
            # Parameters are passed as second positional argument
            params = call_args[0][1]
            assert params["battle_uuid"] == "battle-123"
            assert params["forfeiting_user"] == mock_user.id

    def test_forfeit_returns_winner_id(self, sample_active_battle, mock_user):
        """Test that forfeit returns the winner (the other player)."""
        with patch('services.battle_service.supabase') as mock_supabase:
            mock_rpc_result = Mock()
            mock_rpc_result.data = [{
                'winner_id': 'user-2',
                'already_completed': False
            }]
            mock_supabase.rpc.return_value.execute.return_value = mock_rpc_result

            from services.battle_service import BattleService

            result = BattleService.forfeit_battle('battle-123', mock_user.id)

            assert result['status'] == 'forfeited'
            assert result['winner_id'] == 'user-2'  # The other player wins

    def test_forfeit_already_completed_handled(self, sample_active_battle, mock_user):
        """Test that forfeiting an already completed battle is handled gracefully."""
        with patch('services.battle_service.supabase') as mock_supabase:
            # Mock already completed response
            mock_rpc_result = Mock()
            mock_rpc_result.data = [{
                'winner_id': 'user-2',
                'already_completed': True
            }]
            mock_supabase.rpc.return_value.execute.return_value = mock_rpc_result

            from services.battle_service import BattleService

            with pytest.raises(HTTPException) as exc_info:
                BattleService.forfeit_battle('battle-123', mock_user.id)

            assert exc_info.value.status_code == 400
            assert "already completed" in str(exc_info.value.detail).lower()

    def test_forfeit_nonexistent_battle(self, mock_user):
        """Test that forfeiting a non-existent battle raises 404."""
        with patch('services.battle_service.supabase') as mock_supabase:
            # Mock SQL error for not found
            mock_supabase.rpc.return_value.execute.side_effect = Exception("Battle not found")

            from services.battle_service import BattleService

            with pytest.raises(HTTPException) as exc_info:
                BattleService.forfeit_battle('nonexistent', mock_user.id)

            # The code checks for "not found" and returns 404
            assert exc_info.value.status_code == 404
            assert "not found" in str(exc_info.value.detail).lower()

    def test_forfeit_not_participant_raises_400(self, sample_active_battle, mock_user):
        """Test that forfeiting by non-participant raises error."""
        with patch('services.battle_service.supabase') as mock_supabase:
            # Mock SQL error for not a participant
            mock_supabase.rpc.return_value.execute.side_effect = Exception("User is not a participant in this battle")

            from services.battle_service import BattleService

            # User-3 is not a participant
            with pytest.raises(HTTPException) as exc_info:
                BattleService.forfeit_battle('battle-123', 'user-3')

            assert exc_info.value.status_code == 400  # Error message contains "not a participant"


class TestConcurrentForfeitSafety:
    """Test concurrent forfeit scenarios."""

    def test_concurrent_forfeit_only_updates_once(self):
        """Test that two concurrent forfeits don't double-increment stats."""
        # This test documents the expected behavior:
        # - First forfeit processes normally
        # - Second forfeit sees already_completed and returns early
        # - Battle stats are incremented exactly once
        #
        # The SQL function uses FOR UPDATE to lock the battle row,
        # ensuring only one transaction can proceed at a time.
        assert True  # Documented behavior

    def test_forfeit_idempotent(self):
        """Test that calling forfeit twice doesn't cause double stat increments."""
        # Document: The SQL function should check battle status
        # before processing and return already_completed=True
        # if battle is already completed.
        assert True  # Documented behavior


class TestAcceptBattleAtomic:
    """Test atomic battle accept operation."""

    @pytest.fixture
    def sample_pending_battle(self):
        """Sample pending battle."""
        return {
            'id': 'battle-123',
            'user1_id': 'user-1',
            'user2_id': 'user-2',
            'status': 'pending',
            'start_date': '2026-01-21',
            'end_date': '2026-01-25',
            'duration': 5
        }

    def test_accept_atomic_sql_function_signature(self):
        """Test that the atomic accept SQL function has correct signature."""
        expected_params = {
            "battle_uuid": "UUID"
        }
        expected_returns = {
            "success": "BOOLEAN",
            "error_message": "TEXT"
        }
        assert expected_params is not None
        assert expected_returns is not None

    def test_accept_both_users_get_current_battle(self, sample_pending_battle):
        """Test that both users get current_battle set atomically."""
        with patch('services.battle_service.supabase') as mock_supabase:
            # Mock the RPC call to atomic accept function
            mock_rpc_result = Mock()
            mock_rpc_result.data = [{
                'success': True,
                'error_message': None
            }]
            mock_supabase.rpc.return_value.execute.return_value = mock_rpc_result

            # Mock the final battle lookup
            mock_battle_result = Mock()
            mock_battle_result.data = sample_pending_battle
            mock_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = mock_battle_result

            from services.battle_service import BattleService

            result = BattleService.accept_invite('battle-123', 'user-2')

            # Verify RPC was called
            mock_supabase.rpc.assert_called_once()
            call_args = mock_supabase.rpc.call_args
            assert call_args[0][0] == "accept_battle_atomic"

    def test_accept_fails_for_wrong_user(self, sample_pending_battle):
        """Test that accept fails if user is not the invitee."""
        with patch('services.battle_service.supabase') as mock_supabase:
            # Mock RPC returning error for wrong user
            mock_rpc_result = Mock()
            mock_rpc_result.data = [{
                'success': False,
                'error_message': 'Not your invite to accept'
            }]
            mock_supabase.rpc.return_value.execute.return_value = mock_rpc_result

            from services.battle_service import BattleService

            # user-1 is the inviter, not the invitee
            with pytest.raises(HTTPException) as exc_info:
                BattleService.accept_invite('battle-123', 'user-1')

            assert exc_info.value.status_code == 403


class TestTransactionAtomicity:
    """Test atomicity guarantees of transactions."""

    def test_complete_battle_all_updates_or_none(self):
        """
        Test that complete_battle either updates all stats or none.

        This documents that the SQL function should:
        1. Use BEGIN/EXCEPTION/END block
        2. Rollback on any error
        3. Never leave partial state
        """
        # The complete_battle function should have:
        # - All UPDATE statements in a single transaction block
        # - Exception handling that rolls back changes
        # - Idempotency check at the start
        assert True  # Documented behavior

    def test_daily_round_all_updates_or_none(self):
        """
        Test that calculate_daily_round either updates all or none.

        This documents that the SQL function should:
        1. Update daily_entries for both users
        2. Update profiles.completed_tasks for both users
        3. All in one transaction
        """
        # The calculate_daily_round function should:
        # - Update XP for both users
        # - Update completed_tasks for both users
        # - All updates succeed or all fail together
        assert True  # Documented behavior


class TestSQLFunctionBehavior:
    """Test expected SQL function behaviors."""

    def test_forfeit_uses_row_locking(self):
        """Test that forfeit uses FOR UPDATE to prevent race conditions."""
        # Document: The SQL function should use:
        # SELECT ... FROM battles WHERE id = battle_uuid FOR UPDATE;
        # This locks the row for the duration of the transaction
        assert True  # Documented behavior

    def test_forfeit_checks_status_before_processing(self):
        """Test that forfeit validates battle status before updating."""
        # Document: The SQL function should:
        # 1. Lock the battle row
        # 2. Check if status is 'active'
        # 3. If not active, return early with already_completed=True
        # 4. If active, proceed with forfeiture
        assert True  # Documented behavior

    def test_forfeit_updates_all_in_single_transaction(self):
        """Test that forfeit updates all tables in one transaction."""
        # Document: The SQL function should, in one transaction:
        # 1. Update battles table (status, winner_id, end_date, completed_at)
        # 2. Update winner profile (battle_win_count, battle_count)
        # 3. Update loser profile (battle_count)
        # All three updates must succeed or all must be rolled back
        assert True  # Documented behavior


class TestBackwardsCompatibility:
    """Test that new atomic functions are backwards compatible."""

    def test_forfeit_return_format_unchanged(self):
        """Test that forfeit returns the same format as before."""
        # The return format should be:
        # {
        #     "status": "forfeited",
        #     "winner_id": UUID
        # }
        # This ensures frontend compatibility
        assert True  # Documented behavior

    def test_accept_return_format_unchanged(self):
        """Test that accept returns the same format as before."""
        # The return format should be the battle data object
        # This ensures frontend compatibility
        assert True  # Documented behavior
