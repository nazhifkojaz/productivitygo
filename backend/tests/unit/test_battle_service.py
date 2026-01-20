"""
Unit tests for BattleService.

Tests battle completion idempotency, concurrent access safety,
and atomic operations (forfeit, accept).
"""
import pytest
import concurrent.futures
import threading
from unittest.mock import Mock, patch
from fastapi import HTTPException
from services.battle_service import BattleService


# =============================================================================
# Test Battle Completion Idempotency
# =============================================================================

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


class TestBattleCompletionResponseData:
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


# =============================================================================
# Test Concurrent Battle Completion
# =============================================================================

class TestBattleCompletionRaceCondition:
    """Test that concurrent battle completion calls are safe."""

    def test_concurrent_completion_returns_consistent_results(self):
        """Test multiple threads calling complete_battle simultaneously get consistent results."""
        call_tracker = {
            'count': 0,
            'lock': threading.Lock()
        }

        # Setup: first call completes, subsequent return already_completed
        def rpc_side_effect(*args, **kwargs):
            with call_tracker['lock']:
                idx = call_tracker['count']
                call_tracker['count'] += 1

            if idx == 0:
                # First call actually completes the battle
                return Mock(data=[{
                    'winner_id': 'user-1',
                    'user1_total_xp': 350,
                    'user2_total_xp': 280,
                    'already_completed': False
                }])
            else:
                # Subsequent calls see it as already completed
                return Mock(data=[{
                    'winner_id': 'user-1',
                    'user1_total_xp': 350,
                    'user2_total_xp': 280,
                    'already_completed': True
                }])

        with patch('services.battle_service.supabase') as mock_supabase:
            mock_rpc = Mock()
            mock_rpc.execute.side_effect = rpc_side_effect
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

            # Simulate 5 concurrent calls (e.g., both users + scheduler)
            num_concurrent = 5
            with concurrent.futures.ThreadPoolExecutor(max_workers=num_concurrent) as executor:
                futures = [
                    executor.submit(BattleService.complete_battle, 'battle-123')
                    for _ in range(num_concurrent)
                ]
                results = [f.result() for f in concurrent.futures.as_completed(futures)]

            # Verify all completed successfully
            assert len(results) == num_concurrent

            # All should return the same winner
            winners = [r['winner_id'] for r in results]
            assert all(w == 'user-1' for w in winners), f"Inconsistent winners: {winners}"

            # All should return the same XP values
            user1_xps = [r['scores']['user1_total_xp'] for r in results]
            user2_xps = [r['scores']['user2_total_xp'] for r in results]
            assert all(x == 350 for x in user1_xps), f"Inconsistent user1 XP: {user1_xps}"
            assert all(x == 280 for x in user2_xps), f"Inconsistent user2 XP: {user2_xps}"

            # Exactly one should show already_completed=False (the first)
            fresh_completions = sum(1 for r in results if r.get('already_completed') == False)
            assert fresh_completions == 1, f"Expected 1 fresh completion, got {fresh_completions}"

            # The rest should show already_completed=True
            already_completed_count = sum(1 for r in results if r.get('already_completed') == True)
            assert already_completed_count == num_concurrent - 1

    def test_concurrent_completion_does_not_double_count_stats(self):
        """Verify that concurrent calls don't cause stat inflation (mock test)."""
        # Track how many times the stats would be incremented
        stats_updates = {'count': 0, 'lock': threading.Lock()}

        def rpc_side_effect(*args, **kwargs):
            with stats_updates['lock']:
                if stats_updates['count'] == 0:
                    stats_updates['count'] = 1
                    # First call simulates actual completion with stats update
                    return Mock(data=[{
                        'winner_id': 'user-1',
                        'user1_total_xp': 100,
                        'user2_total_xp': 50,
                        'already_completed': False
                    }])
                else:
                    # Subsequent calls should NOT update stats (already completed)
                    return Mock(data=[{
                        'winner_id': 'user-1',
                        'user1_total_xp': 100,
                        'user2_total_xp': 50,
                        'already_completed': True
                    }])

        with patch('services.battle_service.supabase') as mock_supabase:
            mock_rpc = Mock()
            mock_rpc.execute.side_effect = rpc_side_effect
            mock_supabase.rpc.return_value = mock_rpc

            # Mock battle lookup
            mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = Mock(
                data=[{'id': 'battle-x', 'status': 'active', 'user1_id': 'u1', 'user2_id': 'u2'}]
            )

            # Simulate race: 10 concurrent calls
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(BattleService.complete_battle, 'battle-x') for _ in range(10)]
                results = [f.result() for f in concurrent.futures.as_completed(futures)]

            # All 10 should succeed
            assert len(results) == 10

            # Only 1 should have actually updated stats (already_completed=False)
            actual_updates = sum(1 for r in results if r.get('already_completed') == False)
            assert actual_updates == 1, f"Expected 1 actual stat update, got {actual_updates}"

            # The key assertion: XP values should be consistent
            # If stats were double-counted, later calls would show inflated XP
            final_xps = [r['scores']['user1_total_xp'] for r in results]
            assert all(x == 100 for x in final_xps), f"Stats were inflated! XP values: {final_xps}"


# =============================================================================
# Test Battle Completion Edge Cases
# =============================================================================

class TestBattleCompletionEdgeCases:
    """Test edge cases for battle completion."""

    def test_completion_with_zero_xp_draw(self):
        """Test completion when both users have zero XP (draw)."""
        with patch('services.battle_service.supabase') as mock_supabase:
            mock_rpc = Mock()
            mock_rpc.execute.return_value = Mock(data=[{
                'winner_id': None,  # Draw
                'user1_total_xp': 0,
                'user2_total_xp': 0,
                'already_completed': False
            }])
            mock_supabase.rpc.return_value = mock_rpc

            # Mock battle lookup
            mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = Mock(
                data=[{'id': 'battle-draw', 'status': 'active', 'user1_id': 'u1', 'user2_id': 'u2'}]
            )

            result = BattleService.complete_battle('battle-draw')

            assert result['winner_id'] is None
            assert result['scores']['user1_total_xp'] == 0
            assert result['scores']['user2_total_xp'] == 0

    def test_completion_idempotent_with_draw(self):
        """Test idempotency works correctly with draw (null winner)."""
        calls = 0

        def rpc_side_effect(*args, **kwargs):
            nonlocal calls
            calls += 1
            return Mock(data=[{
                'winner_id': None,
                'user1_total_xp': 100,
                'user2_total_xp': 100,
                'already_completed': calls > 1
            }])

        with patch('services.battle_service.supabase') as mock_supabase:
            mock_rpc = Mock()
            mock_rpc.execute.side_effect = rpc_side_effect
            mock_supabase.rpc.return_value = mock_rpc

            # Mock battle lookup
            mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = Mock(
                data=[{'id': 'battle-draw', 'status': 'active', 'user1_id': 'u1', 'user2_id': 'u2'}]
            )

            result1 = BattleService.complete_battle('battle-draw')
            result2 = BattleService.complete_battle('battle-draw')

            # Both should handle null winner correctly
            assert result1['winner_id'] is None
            assert result2['winner_id'] is None
            assert result2.get('already_completed') == True


# =============================================================================
# Test Forfeit Operation
# =============================================================================

class TestForfeitBattle:
    """Test atomic forfeit battle operation."""

    def test_forfeit_battle_calls_rpc(self, sample_battle_data, mock_user):
        """Test that forfeit_battle calls the atomic SQL RPC function."""
        with patch('services.battle_service.supabase') as mock_supabase:
            # Mock the RPC call to atomic forfeit function
            mock_rpc_result = Mock()
            mock_rpc_result.data = [{
                'winner_id': 'user-2',
                'already_completed': False
            }]
            mock_supabase.rpc.return_value.execute.return_value = mock_rpc_result

            result = BattleService.forfeit_battle('battle-123', mock_user.id)

            # Verify RPC was called with correct parameters
            mock_supabase.rpc.assert_called_once()
            call_args = mock_supabase.rpc.call_args
            assert call_args[0][0] == "forfeit_battle_atomic"
            # Parameters are passed as second positional argument
            params = call_args[0][1]
            assert params["battle_uuid"] == "battle-123"
            assert params["forfeiting_user"] == mock_user.id

    def test_forfeit_returns_winner_id(self, sample_battle_data, mock_user):
        """Test that forfeit returns the winner (the other player)."""
        with patch('services.battle_service.supabase') as mock_supabase:
            mock_rpc_result = Mock()
            mock_rpc_result.data = [{
                'winner_id': 'user-2',
                'already_completed': False
            }]
            mock_supabase.rpc.return_value.execute.return_value = mock_rpc_result

            result = BattleService.forfeit_battle('battle-123', mock_user.id)

            assert result['status'] == 'forfeited'
            assert result['winner_id'] == 'user-2'  # The other player wins

    def test_forfeit_already_completed_handled(self, sample_battle_data, mock_user):
        """Test that forfeiting an already completed battle is handled gracefully."""
        with patch('services.battle_service.supabase') as mock_supabase:
            # Mock already completed response
            mock_rpc_result = Mock()
            mock_rpc_result.data = [{
                'winner_id': 'user-2',
                'already_completed': True
            }]
            mock_supabase.rpc.return_value.execute.return_value = mock_rpc_result

            with pytest.raises(HTTPException) as exc_info:
                BattleService.forfeit_battle('battle-123', mock_user.id)

            assert exc_info.value.status_code == 400
            assert "already completed" in str(exc_info.value.detail).lower()

    def test_forfeit_nonexistent_battle(self, mock_user):
        """Test that forfeiting a non-existent battle raises 404."""
        with patch('services.battle_service.supabase') as mock_supabase:
            # Mock SQL error for not found
            mock_supabase.rpc.return_value.execute.side_effect = Exception("Battle not found")

            with pytest.raises(HTTPException) as exc_info:
                BattleService.forfeit_battle('nonexistent', mock_user.id)

            # The code checks for "not found" and returns 404
            assert exc_info.value.status_code == 404
            assert "not found" in str(exc_info.value.detail).lower()


# =============================================================================
# Test Accept Battle Operation
# =============================================================================

class TestAcceptBattle:
    """Test atomic battle accept operation."""

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

            # user-1 is the inviter, not the invitee
            with pytest.raises(HTTPException) as exc_info:
                BattleService.accept_invite('battle-123', 'user-1')

            assert exc_info.value.status_code == 403
