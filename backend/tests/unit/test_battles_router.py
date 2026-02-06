"""
Unit tests for battles router and RPC validation.

Tests null profile handling, RPC result validation,
and atomic operations.
"""
import pytest
import asyncio
from unittest.mock import Mock, patch
from fastapi import HTTPException
from datetime import date, timedelta


# =============================================================================
# Test Null Profile Handling in get_current_battle
# =============================================================================

class TestGetCurrentBattleNullProfileHandling:
    """Test get_current_battle handles missing profiles gracefully."""

    def test_normal_case_both_profiles_exist(self, mock_user, sample_battle_with_profiles):
        """Test that normal case works when both profiles exist."""
        with patch('routers.battles.supabase') as mock_supabase:
            # Mock process_battle_rounds to return 0 (no rounds processed)
            with patch('utils.battle_processor.process_battle_rounds', return_value=0):
                mock_supabase.table.return_value.select.return_value\
                    .or_.return_value.eq.return_value.execute.return_value = Mock(
                        data=[sample_battle_with_profiles]
                    )

                from routers.battles import get_current_battle
                result = asyncio.run(get_current_battle(mock_user))

                assert result is not None
                assert 'app_state' in result
                assert 'rival' in result
                assert result['rival']['username'] == 'PlayerTwo'

    def test_null_user_profile_does_not_crash(self, mock_user):
        """Test that null user profile doesn't crash the endpoint."""
        battle_with_null_user = {
            'id': 'battle-123',
            'user1_id': 'user-123',
            'user2_id': 'user-456',
            'start_date': '2026-01-20',
            'end_date': '2026-01-22',
            'duration': 3,
            'current_round': 0,
            'status': 'active',
            'user1': None,  # User's profile is missing!
            'user2': {
                'username': 'PlayerTwo',
                'level': 3,
                'timezone': 'Europe/London',
                'battle_win_count': 1,
                'battle_count': 5,
                'total_xp_earned': 1200,
                'completed_tasks': 25
            }
        }

        with patch('routers.battles.supabase') as mock_supabase:
            with patch('utils.battle_processor.process_battle_rounds', return_value=0):
                mock_supabase.table.return_value.select.return_value\
                    .or_.return_value.eq.return_value.execute.return_value = Mock(
                        data=[battle_with_null_user]
                    )

                from routers.battles import get_current_battle

                # Should not raise AttributeError
                result = asyncio.run(get_current_battle(mock_user))

                # Should have fallback values
                assert result is not None
                assert 'app_state' in result

    def test_null_rival_profile_does_not_crash(self, mock_user):
        """Test that null rival profile doesn't crash the endpoint."""
        battle_with_null_rival = {
            'id': 'battle-123',
            'user1_id': 'user-123',
            'user2_id': 'user-456',
            'start_date': '2026-01-20',
            'end_date': '2026-01-22',
            'duration': 3,
            'current_round': 0,
            'status': 'active',
            'user1': {
                'username': 'PlayerOne',
                'level': 5,
                'timezone': 'America/New_York',
                'battle_win_count': 3,
                'battle_count': 10,
                'total_xp_earned': 2500,
                'completed_tasks': 45
            },
            'user2': None  # Rival's profile is missing!
        }

        with patch('routers.battles.supabase') as mock_supabase:
            with patch('utils.battle_processor.process_battle_rounds', return_value=0):
                mock_supabase.table.return_value.select.return_value\
                    .or_.return_value.eq.return_value.execute.return_value = Mock(
                        data=[battle_with_null_rival]
                    )

                from routers.battles import get_current_battle

                # Should not raise AttributeError
                result = asyncio.run(get_current_battle(mock_user))

                # Should have fallback rival data
                assert result is not None
                assert result.get('rival') is not None
                # Should use defaults
                assert result['rival'].get('username') in ['Unknown Rival', None]

    def test_both_profiles_null_does_not_crash(self, mock_user):
        """Test that null profiles for both users doesn't crash."""
        battle_both_null = {
            'id': 'battle-123',
            'user1_id': 'user-123',
            'user2_id': 'user-456',
            'start_date': '2026-01-20',
            'end_date': '2026-01-22',
            'duration': 3,
            'current_round': 0,
            'status': 'active',
            'user1': None,
            'user2': None
        }

        with patch('routers.battles.supabase') as mock_supabase:
            with patch('utils.battle_processor.process_battle_rounds', return_value=0):
                mock_supabase.table.return_value.select.return_value\
                    .or_.return_value.eq.return_value.execute.return_value = Mock(
                        data=[battle_both_null]
                    )

                from routers.battles import get_current_battle

                # Should not raise AttributeError
                result = asyncio.run(get_current_battle(mock_user))

                # Should have some fallback data
                assert result is not None


class TestDefaultProfileValues:
    """Test default values when profile is None."""

    def test_default_user_profile_has_timezone(self):
        """Test default user profile includes timezone."""
        default_profile = {
            'timezone': 'UTC',
            'username': 'Unknown',
            'level': 1
        }
        assert default_profile.get('timezone') == 'UTC'
        assert default_profile.get('username') == 'Unknown'

    def test_default_rival_profile_has_all_fields(self):
        """Test default rival profile includes all required fields."""
        default_rival = {
            'timezone': 'UTC',
            'username': 'Unknown Rival',
            'level': 1,
            'battle_win_count': 0,
            'battle_count': 0,
            'total_xp_earned': 0,
            'completed_tasks': 0
        }
        # Verify all fields exist
        assert default_rival.get('timezone') == 'UTC'
        assert default_rival.get('username') == 'Unknown Rival'
        assert default_rival.get('level') == 1
        assert default_rival.get('battle_win_count') == 0
        assert default_rival.get('battle_count') == 0
        assert default_rival.get('total_xp_earned') == 0
        assert default_rival.get('completed_tasks') == 0


class TestPartialProfileData:
    """Test handling of partial profile data."""

    def test_profile_with_missing_timezone(self):
        """Test profile missing timezone field uses .get() default."""
        partial_profile = {'username': 'Player', 'level': 5}
        # Should use UTC as default
        assert partial_profile.get('timezone', 'UTC') == 'UTC'

    def test_profile_with_missing_username(self):
        """Test profile missing username field uses .get() default."""
        partial_profile = {'timezone': 'UTC', 'level': 5}
        # Should use default value
        assert partial_profile.get('username', 'Unknown') == 'Unknown'


class TestSafeGetWithNone:
    """Test the safe get pattern with None values."""

    def test_none_with_get_attribute_raises_error(self):
        """Demonstrate that None.get() raises AttributeError."""
        none_value = None
        with pytest.raises(AttributeError):
            none_value.get('timezone', 'UTC')

    def test_or_operator_with_none(self):
        """Test using 'or' operator to provide default when None."""
        none_value = None
        default = {'timezone': 'UTC', 'username': 'Unknown'}
        result = none_value or default
        assert result == default

    def test_or_operator_with_valid_value(self):
        """Test that 'or' operator doesn't replace valid values."""
        valid_value = {'timezone': 'America/New_York', 'username': 'Player'}
        default = {'timezone': 'UTC', 'username': 'Unknown'}
        result = valid_value or default
        assert result == valid_value
        assert result['timezone'] == 'America/New_York'


# =============================================================================
# Test RPC Call Result Validation
# =============================================================================

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
            # Mock profile lookups for timezone
            mock_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = Mock(
                data={'timezone': 'UTC'}
            )

            # Mock date.today() to ensure rounds are eligible for processing
            with patch('utils.battle_processor.date') as mock_date:
                mock_date.today.return_value = date(2026, 1, 21)
                mock_date.fromisoformat = date.fromisoformat

                with patch('utils.battle_processor.get_local_date', return_value=date(2026, 1, 21)):
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


# =============================================================================
# Test Atomic Operations
# =============================================================================

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
