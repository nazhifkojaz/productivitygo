"""
Unit tests for invites router.

Tests invite sending, acceptance, rejection, and rematch functionality.
"""
import pytest
import asyncio
from unittest.mock import Mock, patch


class TestGetPendingInvites:
    """Test GET /invites/pending endpoint."""

    def test_returns_pending_invites_for_user(self, mock_user):
        """Test that pending invites are returned for the current user."""
        mock_invites = [
            {
                'id': 'battle-123',
                'user1_id': 'user-456',
                'user2_id': 'user-123',
                'status': 'pending',
                'start_date': '2026-02-10',
                'user1': {'username': 'Challenger'}
            },
            {
                'id': 'battle-124',
                'user1_id': 'user-789',
                'user2_id': 'user-123',
                'status': 'pending',
                'start_date': '2026-02-11',
                'user1': {'username': 'Rival'}
            }
        ]

        with patch('routers.invites.supabase') as mock_supabase:
            mock_supabase.table.return_value.select.return_value\
                .eq.return_value.eq.return_value.execute.return_value = Mock(
                    data=mock_invites
                )

            from routers.invites import get_pending_invites
            result = asyncio.run(get_pending_invites(mock_user))

            assert len(result) == 2
            assert result[0]['status'] == 'pending'
            assert result[0]['user1']['username'] == 'Challenger'

    def test_filters_by_user_id(self, mock_user):
        """Test that invites are filtered by user2_id."""
        with patch('routers.invites.supabase') as mock_supabase:
            mock_supabase.table.return_value.select.return_value\
                .eq.return_value.eq.return_value.execute.return_value = Mock(
                    data=[]
                )

            from routers.invites import get_pending_invites
            asyncio.run(get_pending_invites(mock_user))

            # Verify the correct filter was applied
            mock_supabase.table.return_value.select.return_value\
                .eq.return_value.eq.assert_called_with('status', 'pending')

    def test_returns_empty_list_when_no_invites(self, mock_user):
        """Test that empty list is returned when user has no pending invites."""
        with patch('routers.invites.supabase') as mock_supabase:
            mock_supabase.table.return_value.select.return_value\
                .eq.return_value.eq.return_value.execute.return_value = Mock(
                    data=[]
                )

            from routers.invites import get_pending_invites
            result = asyncio.run(get_pending_invites(mock_user))

            assert result == []


class TestSendInvite:
    """Test POST /invites/send endpoint."""

    def test_creates_battle_invite(self, mock_user):
        """Test that a new invite is created successfully."""
        invite_data = {
            'rival_id': 'rival-123',
            'start_date': '2026-02-15',
            'duration': 5
        }

        mock_battle = {
            'id': 'battle-new',
            'user1_id': mock_user.id,
            'user2_id': 'rival-123',
            'status': 'pending',
            'start_date': '2026-02-15',
            'duration': 5
        }

        with patch('routers.invites.BattleService') as mock_service:
            mock_service.create_invite.return_value = mock_battle

            from routers.invites import send_invite
            from routers.invites import InviteRequest

            result = asyncio.run(send_invite(InviteRequest(**invite_data), mock_user))

            mock_service.create_invite.assert_called_once_with(
                mock_user.id,
                'rival-123',
                '2026-02-15',
                5
            )
            assert result['status'] == 'success'
            assert result['battle']['id'] == 'battle-new'


class TestAcceptBattleInvite:
    """Test POST /invites/{battle_id}/accept endpoint."""

    def test_accepts_pending_battle(self, mock_user):
        """Test that a pending battle is accepted successfully."""
        battle_id = 'battle-123'
        mock_accepted_battle = {
            'id': battle_id,
            'status': 'active',
            'user1_id': 'user-456',
            'user2_id': mock_user.id
        }

        with patch('routers.invites.supabase') as mock_supabase:
            with patch('routers.invites.BattleService') as mock_service:
                mock_service.accept_invite.return_value = None
                mock_supabase.table.return_value.select.return_value\
                    .eq.return_value.single.return_value.execute.return_value = Mock(
                        data=mock_accepted_battle
                    )

                from routers.invites import accept_battle_invite
                result = asyncio.run(accept_battle_invite(battle_id, mock_user))

                mock_service.accept_invite.assert_called_once_with(battle_id, mock_user.id)
                assert result['status'] == 'active'

    def test_returns_updated_battle(self, mock_user):
        """Test that the updated battle is returned after acceptance."""
        battle_id = 'battle-123'
        mock_battle = {
            'id': battle_id,
            'status': 'active',
            'user1_id': 'user-456',
            'user2_id': mock_user.id,
            'start_date': '2026-02-15'
        }

        with patch('routers.invites.supabase') as mock_supabase:
            with patch('routers.invites.BattleService') as mock_service:
                mock_service.accept_invite.return_value = None
                mock_supabase.table.return_value.select.return_value\
                    .eq.return_value.single.return_value.execute.return_value = Mock(
                        data=mock_battle
                    )

                from routers.invites import accept_battle_invite
                result = asyncio.run(accept_battle_invite(battle_id, mock_user))

                assert result['id'] == battle_id
                assert result['status'] == 'active'


class TestRejectBattleInvite:
    """Test POST /invites/{battle_id}/reject endpoint."""

    def test_rejects_pending_battle(self, mock_user):
        """Test that a pending battle is rejected."""
        battle_id = 'battle-123'

        with patch('routers.invites.BattleService') as mock_service:
            mock_service.reject_invite.return_value = {'status': 'rejected'}

            from routers.invites import reject_battle_invite
            result = asyncio.run(reject_battle_invite(battle_id, mock_user))

            mock_service.reject_invite.assert_called_once_with(battle_id, mock_user.id)
            assert result['status'] == 'rejected'


class TestCreateRematch:
    """Test POST /invites/{battle_id}/rematch endpoint."""

    def test_creates_rematch_battle(self, mock_user):
        """Test that a rematch invitation is created."""
        original_battle_id = 'battle-123'

        mock_rematch = {
            'id': 'battle-rematch',
            'user1_id': mock_user.id,
            'user2_id': 'rival-456',
            'status': 'pending',
            'rematch_of': original_battle_id
        }

        with patch('routers.invites.BattleService') as mock_service:
            mock_service.create_rematch.return_value = mock_rematch

            from routers.invites import create_rematch
            result = asyncio.run(create_rematch(original_battle_id, mock_user))

            mock_service.create_rematch.assert_called_once_with(original_battle_id, mock_user.id)
            assert result['rematch_of'] == original_battle_id
            assert result['status'] == 'pending'


class TestGetPendingRematch:
    """Test GET /invites/{battle_id}/pending-rematch endpoint."""

    def test_returns_existing_rematch(self, mock_user):
        """Test that existing pending rematch is returned."""
        battle_id = 'battle-123'

        completed_battle = {
            'id': battle_id,
            'user1_id': 'user-1',
            'user2_id': 'user-2',
            'status': 'completed'
        }

        pending_rematch = {
            'id': 'battle-rematch',
            'user1_id': 'user-1',
            'user2_id': 'user-2',
            'status': 'pending',
            'created_at': '2026-02-05T10:00:00'
        }

        with patch('routers.invites.supabase') as mock_supabase:
            # First call: get completed battle
            mock_supabase.table.return_value.select.return_value\
                .eq.return_value.execute.return_value = Mock(
                    data=[completed_battle]
                )
            # Second call: find pending rematch
            mock_supabase.table.return_value.select.return_value\
                .eq.return_value.or_.return_value.execute.return_value = Mock(
                    data=[pending_rematch]
                )

            from routers.invites import get_pending_rematch
            result = asyncio.run(get_pending_rematch(battle_id, mock_user))

            assert result['exists'] is True
            assert result['battle_id'] == 'battle-rematch'

    def test_identifies_requester(self, mock_user):
        """Test that the endpoint identifies if current user is the requester."""
        battle_id = 'battle-123'

        completed_battle = {
            'id': battle_id,
            'user1_id': mock_user.id,  # Current user is user1
            'user2_id': 'user-2',
            'status': 'completed'
        }

        pending_rematch = {
            'id': 'battle-rematch',
            'user1_id': mock_user.id,  # Current user created the rematch
            'user2_id': 'user-2',
            'status': 'pending',
            'created_at': '2026-02-05T10:00:00'
        }

        with patch('routers.invites.supabase') as mock_supabase:
            mock_supabase.table.return_value.select.return_value\
                .eq.return_value.execute.return_value = Mock(
                    data=[completed_battle]
                )
            mock_supabase.table.return_value.select.return_value\
                .eq.return_value.or_.return_value.execute.return_value = Mock(
                    data=[pending_rematch]
                )

            from routers.invites import get_pending_rematch
            result = asyncio.run(get_pending_rematch(battle_id, mock_user))

            assert result['is_requester'] is True

    def test_returns_not_exists_when_no_rematch(self, mock_user):
        """Test that exists=False is returned when no pending rematch."""
        battle_id = 'battle-123'

        completed_battle = {
            'id': battle_id,
            'user1_id': 'user-1',
            'user2_id': 'user-2',
            'status': 'completed'
        }

        with patch('routers.invites.supabase') as mock_supabase:
            mock_supabase.table.return_value.select.return_value\
                .eq.return_value.execute.return_value = Mock(
                    data=[completed_battle]
                )
            # No pending rematch found
            mock_supabase.table.return_value.select.return_value\
                .eq.return_value.or_.return_value.execute.return_value = Mock(
                    data=[]
                )

            from routers.invites import get_pending_rematch
            result = asyncio.run(get_pending_rematch(battle_id, mock_user))

            assert result['exists'] is False

    def test_handles_reversed_user_order(self, mock_user):
        """Test that rematch is found regardless of user order in original battle."""
        battle_id = 'battle-123'

        # Original battle had user1 as opponent, user2 as current user
        completed_battle = {
            'id': battle_id,
            'user1_id': 'opponent-123',
            'user2_id': mock_user.id,
            'status': 'completed'
        }

        # Rematch has opposite order (current user is now user1)
        pending_rematch = {
            'id': 'battle-rematch',
            'user1_id': mock_user.id,  # Reversed!
            'user2_id': 'opponent-123',
            'status': 'pending',
            'created_at': '2026-02-05T10:00:00'
        }

        with patch('routers.invites.supabase') as mock_supabase:
            mock_supabase.table.return_value.select.return_value\
                .eq.return_value.execute.return_value = Mock(
                    data=[completed_battle]
                )
            # The OR query should match both orderings
            mock_supabase.table.return_value.select.return_value\
                .eq.return_value.or_.return_value.execute.return_value = Mock(
                    data=[pending_rematch]
                )

            from routers.invites import get_pending_rematch
            result = asyncio.run(get_pending_rematch(battle_id, mock_user))

            # Should find the rematch despite reversed user order
            assert result['exists'] is True

    def test_returns_404_for_nonexistent_battle(self, mock_user):
        """Test that 404 is raised when original battle doesn't exist."""
        battle_id = 'nonexistent-battle'

        with patch('routers.invites.supabase') as mock_supabase:
            from routers.invites import get_pending_rematch
            from fastapi import HTTPException

            mock_supabase.table.return_value.select.return_value\
                .eq.return_value.execute.return_value = Mock(
                    data=[]
                )

            with pytest.raises(HTTPException) as exc_info:
                asyncio.run(get_pending_rematch(battle_id, mock_user))

            assert exc_info.value.status_code == 404
            assert exc_info.value.detail == "Battle not found"


class TestDeclineRematch:
    """Test POST /invites/{battle_id}/decline endpoint."""

    def test_declines_rematch(self, mock_user):
        """Test that a rematch invitation is declined."""
        battle_id = 'battle-rematch-123'

        with patch('routers.invites.BattleService') as mock_service:
            mock_service.decline_rematch.return_value = {'status': 'declined'}

            from routers.invites import decline_rematch
            result = asyncio.run(decline_rematch(battle_id, mock_user))

            mock_service.decline_rematch.assert_called_once_with(battle_id)
            assert result['status'] == 'declined'
