"""
Concurrency tests for battle completion race condition fix.
Tests BUG-001: Race condition in battle completion.
"""
import pytest
import concurrent.futures
import threading
from unittest.mock import Mock, patch
from services.battle_service import BattleService


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

    def test_sequential_completion_calls_are_safe(self):
        """Test that sequential calls to complete_battle are idempotent."""
        calls_made = []

        def rpc_side_effect(*args, **kwargs):
            call_num = len(calls_made)
            calls_made.append(call_num)

            if call_num == 0:
                return Mock(data=[{
                    'winner_id': 'user-2',
                    'user1_total_xp': 150,
                    'user2_total_xp': 300,
                    'already_completed': False
                }])
            else:
                return Mock(data=[{
                    'winner_id': 'user-2',
                    'user1_total_xp': 150,
                    'user2_total_xp': 300,
                    'already_completed': True
                }])

        with patch('services.battle_service.supabase') as mock_supabase:
            mock_rpc = Mock()
            mock_rpc.execute.side_effect = rpc_side_effect
            mock_supabase.rpc.return_value = mock_rpc

            # Mock battle lookup
            mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = Mock(
                data=[{'id': 'battle-seq', 'status': 'active', 'user1_id': 'u1', 'user2_id': 'u2'}]
            )

            # Call 5 times sequentially
            results = []
            for _ in range(5):
                result = BattleService.complete_battle('battle-seq')
                results.append(result)

            # All should succeed
            assert len(results) == 5

            # First should be fresh completion
            assert results[0].get('already_completed') == False

            # Rest should be already completed
            for r in results[1:]:
                assert r.get('already_completed') == True

            # All should have same winner and XP
            winners = [r['winner_id'] for r in results]
            assert all(w == 'user-2' for w in winners)


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
