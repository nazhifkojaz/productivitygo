"""
Unit tests for BattleService.

Tests battle completion idempotency, concurrent access safety,
and atomic operations (forfeit, accept).

Updated for async compatibility - all service methods are now async.
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from fastapi import HTTPException
from services.battle_service import BattleService


def _make_mock_supabase(data=None):
    """Helper to create a mock async supabase client."""
    mock = Mock()

    # Create async execute mock
    mock_execute = AsyncMock(return_value=Mock(data=data))
    mock_eq = Mock(return_value=Mock(execute=mock_execute))
    mock_select = Mock(return_value=Mock(eq=mock_eq))
    mock_single = Mock(return_value=Mock(single=Mock(return_value=Mock(execute=mock_execute))))
    mock_table = Mock(return_value=Mock(select=mock_select))
    mock_table.return_value.select.return_value.eq.return_value.execute = mock_execute
    mock_table.return_value.select.return_value.eq.return_value.single.return_value.execute = mock_execute

    mock.table = mock_table
    mock.rpc = Mock(return_value=Mock(execute=mock_execute))

    return mock


# =============================================================================
# Test Battle Completion Idempotency
# =============================================================================

class TestBattleServiceComplete:
    """Test battle completion functionality with idempotency."""

    @pytest.mark.asyncio
    async def test_complete_battle_normal_completion(self):
        """Test normal battle completion returns expected data."""
        result_data = [{
            'winner_id': 'user-1',
            'user1_total_xp': 350,
            'user2_total_xp': 280,
            'already_completed': False
        }]

        mock = _make_mock_supabase(result_data)
        battle_data = {'id': 'battle-123', 'status': 'active', 'user1_id': 'user-1', 'user2_id': 'user-2'}
        mock.table.return_value.select.return_value.eq.return_value.execute = AsyncMock(return_value=Mock(data=[battle_data]))

        with patch('services.battle_service.supabase', mock):
            result = await BattleService.complete_battle('battle-123')

            assert result['status'] == 'completed'
            assert result['winner_id'] == 'user-1'
            assert result['scores']['user1_total_xp'] == 350
            assert result['scores']['user2_total_xp'] == 280
            assert result.get('already_completed') == False

    @pytest.mark.asyncio
    async def test_complete_battle_already_completed_idempotent(self):
        """Test calling complete_battle on already-completed battle returns gracefully."""
        result_data = [{
            'winner_id': 'user-1',
            'user1_total_xp': 350,
            'user2_total_xp': 280,
            'already_completed': True
        }]

        mock = Mock()
        mock_execute = AsyncMock(return_value=Mock(data=result_data))
        mock.rpc.return_value.execute = mock_execute
        battle_data = {'id': 'battle-123', 'status': 'completed', 'user1_id': 'user-1', 'user2_id': 'user-2'}
        mock.table.return_value.select.return_value.eq.return_value.execute = AsyncMock(return_value=Mock(data=[battle_data]))

        with patch('services.battle_service.supabase', mock):
            result = await BattleService.complete_battle('battle-123')

            assert result['status'] == 'completed'
            assert result['winner_id'] == 'user-1'
            assert result.get('already_completed') == True

    @pytest.mark.asyncio
    async def test_complete_battle_double_call_is_idempotent(self):
        """Test that calling complete_battle twice doesn't double-count stats."""
        call_count = {'count': 0}
        rpc_results = [
            {'winner_id': 'user-1', 'user1_total_xp': 350, 'user2_total_xp': 280, 'already_completed': False},
            {'winner_id': 'user-1', 'user1_total_xp': 350, 'user2_total_xp': 280, 'already_completed': True},
        ]

        async def rpc_side_effect(*args, **kwargs):
            idx = call_count['count']
            call_count['count'] += 1
            return Mock(data=[rpc_results[idx]])

        mock = Mock()
        mock_execute = AsyncMock(side_effect=rpc_side_effect)
        mock.rpc.return_value.execute = mock_execute
        battle_data = {'id': 'battle-123', 'status': 'active', 'user1_id': 'user-1', 'user2_id': 'user-2'}
        mock.table.return_value.select.return_value.eq.return_value.execute = AsyncMock(return_value=Mock(data=[battle_data]))

        with patch('services.battle_service.supabase', mock):
            result1 = await BattleService.complete_battle('battle-123')
            result2 = await BattleService.complete_battle('battle-123')

            assert result1['winner_id'] == result2['winner_id']
            assert result1['scores']['user1_total_xp'] == result2['scores']['user1_total_xp']
            assert result1.get('already_completed') == False
            assert result2.get('already_completed') == True

    @pytest.mark.asyncio
    async def test_complete_battle_not_found(self):
        """Test complete_battle raises 404 when battle doesn't exist."""
        mock = Mock()
        mock_execute = AsyncMock(return_value=Mock(data=[None]))
        mock.rpc.return_value.execute = mock_execute
        battle_data = None
        mock.table.return_value.select.return_value.eq.return_value.execute = AsyncMock(return_value=Mock(data=battle_data))

        with patch('services.battle_service.supabase', mock):
            with pytest.raises(HTTPException) as exc_info:
                await BattleService.complete_battle('nonexistent-battle')

            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_complete_battle_invalid_status(self):
        """Test complete_battle raises error for non-active battles."""
        result_data = [{'winner_id': 'user-1', 'user1_total_xp': 100, 'user2_total_xp': 50, 'already_completed': False}]
        mock = Mock()
        mock_execute = AsyncMock(return_value=Mock(data=result_data))
        mock.rpc.return_value.execute = mock_execute
        battle_data = {'id': 'battle-123', 'status': 'pending', 'user1_id': 'user-1', 'user2_id': 'user-2'}
        mock.table.return_value.select.return_value.eq.return_value.execute = AsyncMock(return_value=Mock(data=[battle_data]))

        with patch('services.battle_service.supabase', mock):
            with pytest.raises(HTTPException) as exc_info:
                await BattleService.complete_battle('battle-123')

            assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_complete_battle_rpc_failure(self):
        """Test complete_battle handles RPC failure gracefully."""
        mock = Mock()
        mock_execute = AsyncMock(side_effect=Exception("Database connection lost"))
        mock.rpc.return_value.execute = mock_execute
        battle_data = {'id': 'battle-123', 'status': 'active', 'user1_id': 'user-1', 'user2_id': 'user-2'}
        mock.table.return_value.select.return_value.eq.return_value.execute = AsyncMock(return_value=Mock(data=[battle_data]))

        with patch('services.battle_service.supabase', mock):
            with pytest.raises(HTTPException) as exc_info:
                await BattleService.complete_battle('battle-123')

            assert exc_info.value.status_code == 500


class TestBattleCompletionResponseData:
    """Test response data structure and types."""

    @pytest.mark.asyncio
    async def test_response_has_all_required_fields(self):
        """Test complete_battle response contains all expected fields."""
        result_data = [{
            'winner_id': 'user-1',
            'user1_total_xp': 100,
            'user2_total_xp': 50,
            'already_completed': False
        }]

        mock = _make_mock_supabase(result_data)
        battle_data = {'id': 'battle-123', 'status': 'active', 'user1_id': 'user-1', 'user2_id': 'user-2'}
        mock.table.return_value.select.return_value.eq.return_value.execute = AsyncMock(return_value=Mock(data=[battle_data]))

        with patch('services.battle_service.supabase', mock):
            result = await BattleService.complete_battle('battle-123')

            assert 'status' in result
            assert 'winner_id' in result
            assert 'scores' in result
            assert 'already_completed' in result
            assert 'user1_total_xp' in result['scores']
            assert 'user2_total_xp' in result['scores']

    @pytest.mark.asyncio
    async def test_response_handles_null_winner(self):
        """Test complete_battle handles draw (null winner_id)."""
        result_data = [{
            'winner_id': None,
            'user1_total_xp': 200,
            'user2_total_xp': 200,
            'already_completed': False
        }]

        mock = _make_mock_supabase(result_data)
        battle_data = {'id': 'battle-123', 'status': 'active', 'user1_id': 'user-1', 'user2_id': 'user-2'}
        mock.table.return_value.select.return_value.eq.return_value.execute = AsyncMock(return_value=Mock(data=[battle_data]))

        with patch('services.battle_service.supabase', mock):
            result = await BattleService.complete_battle('battle-123')

            assert result['winner_id'] is None
            assert result['scores']['user1_total_xp'] == result['scores']['user2_total_xp']


class TestBattleCompletionRaceCondition:
    """Test that concurrent battle completion calls are safe."""

    @pytest.mark.asyncio
    async def test_concurrent_completion_returns_consistent_results(self):
        """Test multiple threads calling complete_battle simultaneously get consistent results."""
        call_tracker = {'count': 0}

        async def rpc_side_effect(*args, **kwargs):
            idx = call_tracker['count']
            call_tracker['count'] += 1

            if idx == 0:
                return Mock(data=[{
                    'winner_id': 'user-1',
                    'user1_total_xp': 350,
                    'user2_total_xp': 280,
                    'already_completed': False
                }])
            else:
                return Mock(data=[{
                    'winner_id': 'user-1',
                    'user1_total_xp': 350,
                    'user2_total_xp': 280,
                    'already_completed': True
                }])

        mock = Mock()
        mock_execute = AsyncMock(side_effect=rpc_side_effect)
        mock.rpc.return_value.execute = mock_execute
        battle_data = {'id': 'battle-123', 'status': 'active', 'user1_id': 'user-1', 'user2_id': 'user-2'}
        mock.table.return_value.select.return_value.eq.return_value.execute = AsyncMock(return_value=Mock(data=[battle_data]))

        with patch('services.battle_service.supabase', mock):
            # Simulate 5 concurrent calls using asyncio.gather instead of ThreadPoolExecutor
            num_concurrent = 5
            results = await asyncio.gather(*[
                BattleService.complete_battle('battle-123')
                for _ in range(num_concurrent)
            ])

            assert len(results) == num_concurrent
            winners = [r['winner_id'] for r in results]
            assert all(w == 'user-1' for w in winners)

            fresh_completions = sum(1 for r in results if r.get('already_completed') == False)
            assert fresh_completions == 1

    @pytest.mark.asyncio
    async def test_concurrent_completion_does_not_double_count_stats(self):
        """Verify that concurrent calls don't cause stat inflation (mock test)."""
        stats_updates = {'count': 0}

        async def rpc_side_effect(*args, **kwargs):
            if stats_updates['count'] == 0:
                stats_updates['count'] = 1
                return Mock(data=[{
                    'winner_id': 'user-1',
                    'user1_total_xp': 100,
                    'user2_total_xp': 50,
                    'already_completed': False
                }])
            else:
                return Mock(data=[{
                    'winner_id': 'user-1',
                    'user1_total_xp': 100,
                    'user2_total_xp': 50,
                    'already_completed': True
                }])

        mock = Mock()
        mock_execute = AsyncMock(side_effect=rpc_side_effect)
        mock.rpc.return_value.execute = mock_execute
        battle_data = {'id': 'battle-x', 'status': 'active', 'user1_id': 'u1', 'user2_id': 'u2'}
        mock.table.return_value.select.return_value.eq.return_value.execute = AsyncMock(return_value=Mock(data=[battle_data]))

        with patch('services.battle_service.supabase', mock):
            results = await asyncio.gather(*[
                BattleService.complete_battle('battle-x')
                for _ in range(10)
            ])

            assert len(results) == 10
            actual_updates = sum(1 for r in results if r.get('already_completed') == False)
            assert actual_updates == 1

            final_xps = [r['scores']['user1_total_xp'] for r in results]
            assert all(x == 100 for x in final_xps)


class TestBattleCompletionEdgeCases:
    """Test edge cases for battle completion."""

    @pytest.mark.asyncio
    async def test_completion_with_zero_xp_draw(self):
        """Test completion when both users have zero XP (draw)."""
        result_data = [{
            'winner_id': None,
            'user1_total_xp': 0,
            'user2_total_xp': 0,
            'already_completed': False
        }]

        mock = _make_mock_supabase(result_data)
        battle_data = {'id': 'battle-draw', 'status': 'active', 'user1_id': 'u1', 'user2_id': 'u2'}
        mock.table.return_value.select.return_value.eq.return_value.execute = AsyncMock(return_value=Mock(data=[battle_data]))

        with patch('services.battle_service.supabase', mock):
            result = await BattleService.complete_battle('battle-draw')

            assert result['winner_id'] is None
            assert result['scores']['user1_total_xp'] == 0
            assert result['scores']['user2_total_xp'] == 0

    @pytest.mark.asyncio
    async def test_completion_idempotent_with_draw(self):
        """Test idempotency works correctly with draw (null winner)."""
        calls = 0

        async def rpc_side_effect(*args, **kwargs):
            nonlocal calls
            calls += 1
            return Mock(data=[{
                'winner_id': None,
                'user1_total_xp': 100,
                'user2_total_xp': 100,
                'already_completed': calls > 1
            }])

        mock = Mock()
        mock_execute = AsyncMock(side_effect=rpc_side_effect)
        mock.rpc.return_value.execute = mock_execute
        battle_data = {'id': 'battle-draw', 'status': 'active', 'user1_id': 'u1', 'user2_id': 'u2'}
        mock.table.return_value.select.return_value.eq.return_value.execute = AsyncMock(return_value=Mock(data=[battle_data]))

        with patch('services.battle_service.supabase', mock):
            result1 = await BattleService.complete_battle('battle-draw')
            result2 = await BattleService.complete_battle('battle-draw')

            assert result1['winner_id'] is None
            assert result2['winner_id'] is None
            assert result2.get('already_completed') == True


class TestForfeitBattle:
    """Test atomic forfeit battle operation."""

    @pytest.mark.asyncio
    async def test_forfeit_battle_calls_rpc(self):
        """Test that forfeit_battle calls the atomic SQL RPC function."""
        result_data = [{'winner_id': 'user-2', 'already_completed': False}]

        mock = Mock()
        mock_execute = AsyncMock(return_value=Mock(data=result_data))
        mock.rpc.return_value.execute = mock_execute

        with patch('services.battle_service.supabase', mock):
            result = await BattleService.forfeit_battle('battle-123', 'user-1')

            mock.rpc.assert_called_once()
            call_args = mock.rpc.call_args
            assert call_args[0][0] == "forfeit_battle_atomic"
            params = call_args[0][1]
            assert params["battle_uuid"] == "battle-123"
            assert params["forfeiting_user"] == "user-1"

    @pytest.mark.asyncio
    async def test_forfeit_returns_winner_id(self):
        """Test that forfeit returns the winner (the other player)."""
        result_data = [{'winner_id': 'user-2', 'already_completed': False}]

        mock = Mock()
        mock_execute = AsyncMock(return_value=Mock(data=result_data))
        mock.rpc.return_value.execute = mock_execute

        with patch('services.battle_service.supabase', mock):
            result = await BattleService.forfeit_battle('battle-123', 'user-1')

            assert result['status'] == 'forfeited'
            assert result['winner_id'] == 'user-2'

    @pytest.mark.asyncio
    async def test_forfeit_already_completed_handled(self):
        """Test that forfeiting an already completed battle is handled gracefully."""
        result_data = [{'winner_id': 'user-2', 'already_completed': True}]

        mock = Mock()
        mock_execute = AsyncMock(return_value=Mock(data=result_data))
        mock.rpc.return_value.execute = mock_execute

        with patch('services.battle_service.supabase', mock):
            with pytest.raises(HTTPException) as exc_info:
                await BattleService.forfeit_battle('battle-123', 'user-1')

            assert exc_info.value.status_code == 400
            assert "already completed" in str(exc_info.value.detail).lower()

    @pytest.mark.asyncio
    async def test_forfeit_nonexistent_battle(self):
        """Test that forfeiting a non-existent battle raises 404."""
        mock = Mock()
        mock_execute = AsyncMock(side_effect=Exception("Battle not found"))
        mock.rpc.return_value.execute = mock_execute

        with patch('services.battle_service.supabase', mock):
            with pytest.raises(HTTPException) as exc_info:
                await BattleService.forfeit_battle('nonexistent', 'user-1')

            assert exc_info.value.status_code == 404


class TestAcceptBattle:
    """Test atomic battle accept operation."""

    @pytest.mark.asyncio
    async def test_accept_both_users_get_current_battle(self):
        """Test that both users get current_battle set atomically."""
        result_data = [{'success': True, 'error_message': None}]
        battle_data = {'id': 'battle-123', 'status': 'active', 'user1_id': 'user-1', 'user2_id': 'user-2'}

        mock = Mock()
        mock_execute = AsyncMock(return_value=Mock(data=result_data))
        mock.rpc.return_value.execute = mock_execute
        mock_battle_execute = AsyncMock(return_value=Mock(data=[battle_data]))
        mock.table.return_value.select.return_value.eq.return_value.single.return_value.execute = mock_battle_execute

        with patch('services.battle_service.supabase', mock):
            result = await BattleService.accept_invite('battle-123', 'user-2')

            mock.rpc.assert_called_once()
            call_args = mock.rpc.call_args
            assert call_args[0][0] == "accept_battle_atomic"

    @pytest.mark.asyncio
    async def test_accept_fails_for_wrong_user(self):
        """Test that accept fails if user is not the invitee."""
        result_data = [{'success': False, 'error_message': 'Not your invite to accept'}]

        mock = Mock()
        mock_execute = AsyncMock(return_value=Mock(data=result_data))
        mock.rpc.return_value.execute = mock_execute

        with patch('services.battle_service.supabase', mock):
            with pytest.raises(HTTPException) as exc_info:
                await BattleService.accept_invite('battle-123', 'user-1')

            assert exc_info.value.status_code == 403
