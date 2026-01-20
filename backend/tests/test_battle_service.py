"""
Unit tests for BattleService.complete_battle() idempotency.
Tests BUG-001 fix: Race condition in battle completion.
"""
import pytest
from unittest.mock import Mock, patch, call
from services.battle_service import BattleService


class TestBattleServiceComplete:
    """Test battle completion functionality with idempotency."""

    def test_complete_battle_normal_completion(self, mock_supabase, sample_completion_result):
        """Test normal battle completion returns expected data."""
        # Setup mock
        mock_rpc = Mock()
        mock_rpc.execute.return_value = Mock(data=[sample_completion_result])
        mock_supabase.rpc.return_value = mock_rpc

        # Mock battle lookup
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = Mock(
            data=[{
                'id': 'battle-123',
                'status': 'active',
                'user1_id': 'user-1',
                'user2_id': 'user-2'
            }]
        )

        # Execute
        result = BattleService.complete_battle('battle-123')

        # Assert
        assert result['status'] == 'completed'
        assert result['winner_id'] == 'user-1'
        assert result['scores']['user1_total_xp'] == 350
        assert result['scores']['user2_total_xp'] == 280
        assert result.get('already_completed') == False

        # Verify RPC was called correctly
        mock_supabase.rpc.assert_called_once_with('complete_battle', {'battle_uuid': 'battle-123'})

    def test_complete_battle_already_completed_idempotent(self, mock_supabase, sample_already_completed_result):
        """Test calling complete_battle on already-completed battle returns gracefully."""
        # Setup mock - battle is already completed in DB
        mock_rpc = Mock()
        mock_rpc.execute.return_value = Mock(data=[sample_already_completed_result])
        mock_supabase.rpc.return_value = mock_rpc

        # Mock battle lookup
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = Mock(
            data=[{
                'id': 'battle-123',
                'status': 'completed',  # Already completed
                'user1_id': 'user-1',
                'user2_id': 'user-2'
            }]
        )

        # Execute
        result = BattleService.complete_battle('battle-123')

        # Assert - should still return success data
        assert result['status'] == 'completed'
        assert result['winner_id'] == 'user-1'
        assert result.get('already_completed') == True

    def test_complete_battle_double_call_is_idempotent(self, mock_supabase, sample_battle_data):
        """Test that calling complete_battle twice doesn't double-count stats."""
        call_count = {'count': 0}
        rpc_results = [
            {'winner_id': 'user-1', 'user1_total_xp': 350, 'user2_total_xp': 280, 'already_completed': False},
            {'winner_id': 'user-1', 'user1_total_xp': 350, 'user2_total_xp': 280, 'already_completed': True},
        ]

        def side_effect(*args, **kwargs):
            idx = call_count['count']
            call_count['count'] += 1
            return Mock(data=[rpc_results[idx]])

        # Setup mock
        mock_rpc = Mock()
        mock_rpc.execute.side_effect = side_effect
        mock_supabase.rpc.return_value = mock_rpc

        # Mock battle lookup - returns active battle (simulates race condition)
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = Mock(
            data=[sample_battle_data]
        )

        # Execute twice (simulating concurrent calls)
        result1 = BattleService.complete_battle('battle-123')
        result2 = BattleService.complete_battle('battle-123')

        # Both should return the same winner and XP
        assert result1['winner_id'] == result2['winner_id']
        assert result1['scores']['user1_total_xp'] == result2['scores']['user1_total_xp']
        assert result1['scores']['user2_total_xp'] == result2['scores']['user2_total_xp']

        # First call should indicate fresh completion
        assert result1.get('already_completed') == False

        # Second call should indicate it was already completed
        assert result2.get('already_completed') == True

        # RPC should be called twice
        assert mock_supabase.rpc.call_count == 2

    def test_complete_battle_not_found(self, mock_supabase):
        """Test complete_battle raises 404 when battle doesn't exist."""
        # Setup mock - battle not found
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = Mock(
            data=None
        )

        # Execute and assert
        with pytest.raises(Exception) as exc_info:
            BattleService.complete_battle('nonexistent-battle')

        # The actual exception comes from HTTPException in the service
        assert 'not found' in str(exc_info.value).lower() or '404' in str(exc_info.value)

    def test_complete_battle_invalid_status(self, mock_supabase):
        """Test complete_battle raises error for non-active battles."""
        # Setup mock - battle already completed
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = Mock(
            data=[{
                'id': 'battle-123',
                'status': 'pending',  # Not active
                'user1_id': 'user-1',
                'user2_id': 'user-2'
            }]
        )

        # Execute and assert
        with pytest.raises(Exception) as exc_info:
            BattleService.complete_battle('battle-123')

        # Should get an error about battle not being active
        assert 'not active' in str(exc_info.value).lower() or '400' in str(exc_info.value)

    def test_complete_battle_rpc_failure(self, mock_supabase, sample_battle_data):
        """Test complete_battle handles RPC failure gracefully."""
        # Setup mock - RPC fails
        mock_rpc = Mock()
        mock_rpc.execute.side_effect = Exception("Database connection lost")
        mock_supabase.rpc.return_value = mock_rpc

        # Mock battle lookup
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = Mock(
            data=[sample_battle_data]
        )

        # Execute and assert
        with pytest.raises(Exception) as exc_info:
            BattleService.complete_battle('battle-123')

        assert 'error completing battle' in str(exc_info.value).lower()


class TestBattleServiceCompleteResponseData:
    """Test response data structure and types."""

    def test_response_has_all_required_fields(self, mock_supabase):
        """Test complete_battle response contains all expected fields."""
        # Setup mock
        mock_rpc = Mock()
        mock_rpc.execute.return_value = Mock(data=[{
            'winner_id': 'user-1',
            'user1_total_xp': 100,
            'user2_total_xp': 50,
            'already_completed': False
        }])
        mock_supabase.rpc.return_value = mock_rpc

        # Mock battle lookup
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = Mock(
            data=[{'id': 'battle-123', 'status': 'active', 'user1_id': 'user-1', 'user2_id': 'user-2'}]
        )

        # Execute
        result = BattleService.complete_battle('battle-123')

        # Assert all fields present
        assert 'status' in result
        assert 'winner_id' in result
        assert 'scores' in result
        assert 'already_completed' in result
        assert 'user1_total_xp' in result['scores']
        assert 'user2_total_xp' in result['scores']

    def test_response_handles_null_winner(self, mock_supabase):
        """Test complete_battle handles draw (null winner_id)."""
        # Setup mock - draw scenario
        mock_rpc = Mock()
        mock_rpc.execute.return_value = Mock(data=[{
            'winner_id': None,  # Draw
            'user1_total_xp': 200,
            'user2_total_xp': 200,
            'already_completed': False
        }])
        mock_supabase.rpc.return_value = mock_rpc

        # Mock battle lookup
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = Mock(
            data=[{'id': 'battle-123', 'status': 'active', 'user1_id': 'user-1', 'user2_id': 'user-2'}]
        )

        # Execute
        result = BattleService.complete_battle('battle-123')

        # Assert
        assert result['winner_id'] is None
        assert result['scores']['user1_total_xp'] == result['scores']['user2_total_xp']
