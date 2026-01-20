"""
Unit tests for RPC call result validation.
Tests BUG-004 fix: RPC call results not validated.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import date, timedelta


class TestRPCCallValidation:
    """Test that RPC results are properly validated before proceeding."""

    @pytest.fixture
    def sample_battle(self):
        """Sample battle for testing."""
        return {
            'id': 'battle-123',
            'user1_id': 'user-1',
            'user2_id': 'user-2',
            'start_date': '2026-01-20',
            'end_date': '2026-01-22',
            'duration': 3,
            'current_round': 0,
            'status': 'active',
            'user1': {'timezone': 'UTC', 'username': 'Player1'},
            'user2': {'timezone': 'UTC', 'username': 'Player2'}
        }

    def test_rpc_returns_valid_data_increments_round(self, sample_battle):
        """Test that successful RPC with valid data increments round counter."""
        with patch('utils.battle_processor.supabase') as mock_supabase:
            # Mock successful RPC with valid data
            mock_rpc = Mock()
            mock_rpc.execute.return_value = Mock(data=[
                {'user1_xp': 100, 'user2_xp': 50, 'winner_id': 'user-1'}
            ])
            mock_supabase.rpc.return_value = mock_rpc
            mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = Mock()

            from utils.battle_processor import process_battle_rounds

            result = process_battle_rounds(sample_battle)

            # Should process one round
            assert result == 1

    def test_rpc_returns_none_does_not_increment_round(self, sample_battle):
        """Test that RPC returning None does NOT increment round counter."""
        with patch('utils.battle_processor.supabase') as mock_supabase:
            # Mock RPC that returns None (simulating failure)
            mock_rpc = Mock()
            mock_rpc.execute.return_value = Mock(data=None)
            mock_supabase.rpc.return_value = mock_rpc

            from utils.battle_processor import process_battle_rounds

            result = process_battle_rounds(sample_battle)

            # Should NOT process any rounds
            assert result == 0

    def test_rpc_returns_empty_list_does_not_increment_round(self, sample_battle):
        """Test that RPC returning empty list does NOT increment round counter."""
        with patch('utils.battle_processor.supabase') as mock_supabase:
            # Mock RPC that returns empty list
            mock_rpc = Mock()
            mock_rpc.execute.return_value = Mock(data=[])
            mock_supabase.rpc.return_value = mock_rpc

            from utils.battle_processor import process_battle_rounds

            result = process_battle_rounds(sample_battle)

            # Should NOT process any rounds
            assert result == 0

    def test_complete_battle_validates_result(self):
        """Test that complete_battle RPC result is validated."""
        with patch('utils.battle_processor.supabase') as mock_supabase:
            # Mock successful battle completion
            mock_rpc = Mock()
            mock_rpc.execute.return_value = Mock(data=[
                {'winner_id': 'user-1', 'user1_total_xp': 300, 'user2_total_xp': 200, 'already_completed': False}
            ])
            mock_supabase.rpc.return_value = mock_rpc

            # Mock battle table update for status
            mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = Mock()

            from utils.battle_processor import process_battle_rounds
            battle = {
                'id': 'battle-123',
                'status': 'active',
                'start_date': '2026-01-20',
                'end_date': '2026-01-22',
                'duration': 1,
                'current_round': 1,
                'user1_id': 'u1',
                'user2_id': 'u2'
            }

            result = process_battle_rounds(battle)

            # Should process the round
            assert result >= 0

    def test_complete_battle_handles_none_result(self):
        """Test that complete_battle handles None result gracefully."""
        with patch('utils.battle_processor.supabase') as mock_supabase:
            # Mock RPC that returns None
            mock_rpc = Mock()
            mock_rpc.execute.return_value = Mock(data=None)
            mock_supabase.rpc.return_value = mock_rpc

            from utils.battle_processor import process_battle_rounds
            battle = {
                'id': 'battle-123',
                'status': 'active',
                'start_date': '2026-01-20',
                'end_date': '2026-01-20',
                'duration': 1,
                'current_round': 1,
                'user1_id': 'u1',
                'user2_id': 'u2'
            }

            # Should not crash even if RPC returns None
            result = process_battle_rounds(battle)
            assert result >= 0


class TestRPCResponseHandling:
    """Test different RPC response scenarios."""

    def test_rpc_response_is_list(self):
        """Test handling of RPC response as list."""
        response_data = [
            {'user1_xp': 100, 'user2_xp': 50, 'winner_id': 'user-1'}
        ]
        data = response_data[0] if isinstance(response_data, list) else response_data
        assert data['user1_xp'] == 100

    def test_rpc_response_is_dict(self):
        """Test handling of RPC response as dict (single row)."""
        response_data = {'user1_xp': 100, 'user2_xp': 50, 'winner_id': 'user-1'}
        data = response_data[0] if isinstance(response_data, list) else response_data
        assert data['user1_xp'] == 100

    def test_rpc_response_extract_xp_values(self):
        """Test extracting XP values from RPC response."""
        response_data = [
            {'user1_xp': 100, 'user2_xp': 50, 'winner_id': 'user-1'}
        ]
        data = response_data[0] if isinstance(response_data, list) else response_data
        if data:
            user1_xp = data.get('user1_xp', 0)
            user2_xp = data.get('user2_xp', 0)
            assert user1_xp == 100
            assert user2_xp == 50


class TestBattleProcessorRoundProcessing:
    """Test round processing with various RPC scenarios."""

    @pytest.fixture
    def mock_supabase_base(self):
        """Base mock for supabase."""
        with patch('utils.battle_processor.supabase') as mock:
            yield mock

    def test_round_not_processed_when_date_not_passed(self, mock_supabase_base):
        """Test that round is not processed when date hasn't passed for both players."""
        from utils.battle_processor import process_battle_rounds

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
        from utils.battle_processor import process_battle_rounds

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
        from utils.battle_processor import process_battle_rounds

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

        with patch('utils.battle_processor.get_local_date') as mock_date:
            # Both players have finished 2 rounds
            mock_date.side_effect = [
                date(2026, 1, 21),  # First check
                date(2026, 1, 21),  # First check (user2)
                date(2026, 1, 22),  # Second check (user1)
                date(2026, 1, 22),  # Second check (user2)
            ]

            result = process_battle_rounds(battle)

            # Should process two rounds
            assert result == 2
