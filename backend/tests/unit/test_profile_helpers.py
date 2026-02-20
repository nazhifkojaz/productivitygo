"""
Unit tests for profile helper utilities.

Tests for centralized user profile response builders and rival
enrichment functions extracted from duplicate implementations.

REFACTOR-007: Phase 2 Items 2.3, 2.4
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from utils.profile_helpers import (
    build_user_profiles_list,
    batch_fetch_rival_usernames,
    enrich_battle_history
)


class TestBuildUserProfilesList:
    """Test build_user_profiles_list utility function."""

    def test_full_profile_data(self):
        """Test with complete profile data."""
        profiles = [
            {
                'id': 'abc123',
                'username': 'player1',
                'level': 12,  # Changed from 5 to meet Challenger requirement (level >= 11)
                'battle_count': 10,
                'battle_win_count': 6,
                'avatar_emoji': '😀'
            }
        ]
        result = build_user_profiles_list(profiles)

        assert len(result) == 1
        assert result[0]['id'] == 'abc123'
        assert result[0]['username'] == 'player1'
        assert result[0]['level'] == 12
        assert result[0]['rank'] == 'Challenger'  # Level 12, 5+ battles = Challenger
        assert result[0]['avatar_url'] is None
        assert result[0]['avatar_emoji'] == '😀'

    def test_missing_fields_use_defaults(self):
        """Test with missing profile fields."""
        profiles = [
            {'id': 'xyz789'}  # Only required field
        ]
        result = build_user_profiles_list(profiles)

        assert len(result) == 1
        assert result[0]['id'] == 'xyz789'
        assert result[0]['username'] == 'Unknown'
        assert result[0]['level'] == 1
        assert result[0]['rank'] == 'Novice'
        assert result[0]['avatar_emoji'] == '😀'

    def test_empty_list_returns_empty(self):
        """Test with empty list."""
        result = build_user_profiles_list([])
        assert result == []

    def test_multiple_profiles(self):
        """Test with multiple profiles."""
        profiles = [
            {
                'id': 'user1',
                'username': 'Alice',
                'level': 10,
                'battle_count': 20,
                'battle_win_count': 15,
                'avatar_emoji': '🎮'
            },
            {
                'id': 'user2',
                'username': 'Bob',
                'level': 3,
                'battle_count': 5,
                'battle_win_count': 1,
                'avatar_emoji': '🎯'
            }
        ]
        result = build_user_profiles_list(profiles)

        assert len(result) == 2
        assert result[0]['username'] == 'Alice'
        assert result[1]['username'] == 'Bob'

    def test_none_level_defaults_to_1(self):
        """Test with None level."""
        profiles = [
            {
                'id': 'test',
                'level': None,
                'battle_count': 0,
                'battle_win_count': 0
            }
        ]
        result = build_user_profiles_list(profiles)
        assert result[0]['level'] == 1

    def test_zero_battle_count(self):
        """Test with zero battle count."""
        profiles = [
            {
                'id': 'newbie',
                'username': 'NewPlayer',
                'level': 1,
                'battle_count': 0,
                'battle_win_count': 0
            }
        ]
        result = build_user_profiles_list(profiles)
        assert result[0]['rank'] == 'Novice'


class TestBatchFetchRivalUsernames:
    """Test batch_fetch_rival_usernames utility function."""

    @pytest.mark.asyncio
    async def test_single_rival(self):
        """Test fetching a single rival."""
        match_history = [
            {'user1_id': 'me', 'user2_id': 'rival1'}
        ]

        mock_response = MagicMock()
        mock_response.data = [
            {'id': 'rival1', 'username': 'Player One'}
        ]

        with patch('utils.profile_helpers.supabase') as mock_supabase:
            mock_supabase.table.return_value.select.return_value.in_.return_value.execute.return_value = (
                AsyncMock(return_value=mock_response)()
            )

            result = await batch_fetch_rival_usernames(match_history, 'me')

            assert result == {'rival1': 'Player One'}

    @pytest.mark.asyncio
    async def test_multiple_rivals(self):
        """Test fetching multiple rivals."""
        match_history = [
            {'user1_id': 'me', 'user2_id': 'rival1'},
            {'user1_id': 'rival2', 'user2_id': 'me'},
            {'user1_id': 'me', 'user2_id': 'rival3'}
        ]

        mock_response = MagicMock()
        mock_response.data = [
            {'id': 'rival1', 'username': 'Player One'},
            {'id': 'rival2', 'username': 'Player Two'},
            {'id': 'rival3', 'username': 'Player Three'}
        ]

        with patch('utils.profile_helpers.supabase') as mock_supabase:
            mock_supabase.table.return_value.select.return_value.in_.return_value.execute.return_value = (
                AsyncMock(return_value=mock_response)()
            )

            result = await batch_fetch_rival_usernames(match_history, 'me')

            assert result == {
                'rival1': 'Player One',
                'rival2': 'Player Two',
                'rival3': 'Player Three'
            }

    @pytest.mark.asyncio
    async def test_empty_history(self):
        """Test with empty match history."""
        result = await batch_fetch_rival_usernames([], 'me')
        assert result == {}

    @pytest.mark.asyncio
    async def test_same_rival_multiple_times(self):
        """Test that same rival appears only once in result."""
        match_history = [
            {'user1_id': 'me', 'user2_id': 'rival1'},
            {'user1_id': 'rival1', 'user2_id': 'me'},
            {'user1_id': 'me', 'user2_id': 'rival1'}
        ]

        mock_response = MagicMock()
        mock_response.data = [
            {'id': 'rival1', 'username': 'Recurring Rival'}
        ]

        with patch('utils.profile_helpers.supabase') as mock_supabase:
            mock_supabase.table.return_value.select.return_value.in_.return_value.execute.return_value = (
                AsyncMock(return_value=mock_response)()
            )

            result = await batch_fetch_rival_usernames(match_history, 'me')

            assert result == {'rival1': 'Recurring Rival'}

    @pytest.mark.asyncio
    async def test_rival_id_detection_user1(self):
        """Test rival detection when user is user2."""
        match_history = [
            {'user1_id': 'rival1', 'user2_id': 'me'}
        ]

        mock_response = MagicMock()
        mock_response.data = [
            {'id': 'rival1', 'username': 'Challenger'}
        ]

        with patch('utils.profile_helpers.supabase') as mock_supabase:
            mock_supabase.table.return_value.select.return_value.in_.return_value.execute.return_value = (
                AsyncMock(return_value=mock_response)()
            )

            result = await batch_fetch_rival_usernames(match_history, 'me')

            assert result == {'rival1': 'Challenger'}


class TestEnrichBattleHistory:
    """Test enrich_battle_history utility function."""

    def test_win_result(self):
        """Test enrichment when user wins."""
        match_history = [{
            'id': 'battle1',
            'user1_id': 'me',
            'user2_id': 'rival1',
            'winner_id': 'me',
            'end_date': '2026-02-18',
            'duration': 5
        }]
        rivals_map = {'rival1': 'Player One'}

        result = enrich_battle_history(match_history, 'me', rivals_map)

        assert len(result) == 1
        assert result[0]['id'] == 'battle1'
        assert result[0]['result'] == 'WIN'
        assert result[0]['rival'] == 'Player One'
        assert result[0]['duration'] == 5

    def test_loss_result(self):
        """Test enrichment when user loses."""
        match_history = [{
            'id': 'battle1',
            'user1_id': 'me',
            'user2_id': 'rival1',
            'winner_id': 'rival1',
            'end_date': '2026-02-18',
            'duration': 3
        }]
        rivals_map = {'rival1': 'Player One'}

        result = enrich_battle_history(match_history, 'me', rivals_map)

        assert len(result) == 1
        assert result[0]['result'] == 'LOSS'

    def test_draw_result(self):
        """Test enrichment when battle is a draw."""
        match_history = [{
            'id': 'battle1',
            'user1_id': 'me',
            'user2_id': 'rival1',
            'winner_id': None,  # No winner
            'end_date': '2026-02-18',
            'duration': 5
        }]
        rivals_map = {'rival1': 'Player One'}

        result = enrich_battle_history(match_history, 'me', rivals_map)

        assert len(result) == 1
        assert result[0]['result'] == 'DRAW'

    def test_draw_result_third_party_winner(self):
        """Test draw when someone else won (shouldn't happen but handle it)."""
        match_history = [{
            'id': 'battle1',
            'user1_id': 'me',
            'user2_id': 'rival1',
            'winner_id': 'someone_else',
            'end_date': '2026-02-18',
            'duration': 5
        }]
        rivals_map = {'rival1': 'Player One'}

        result = enrich_battle_history(match_history, 'me', rivals_map)

        assert result[0]['result'] == 'DRAW'

    def test_include_type_true(self):
        """Test include_type parameter adds type field."""
        match_history = [{
            'id': 'battle1',
            'user1_id': 'me',
            'user2_id': 'rival1',
            'winner_id': 'me',
            'end_date': '2026-02-18',
            'duration': 5
        }]
        rivals_map = {'rival1': 'Player One'}

        result = enrich_battle_history(match_history, 'me', rivals_map, include_type=True)

        assert 'type' in result[0]
        assert result[0]['type'] == 'battle'

    def test_include_type_false(self):
        """Test include_type=False omits type field."""
        match_history = [{
            'id': 'battle1',
            'user1_id': 'me',
            'user2_id': 'rival1',
            'winner_id': 'me',
            'end_date': '2026-02-18',
            'duration': 5
        }]
        rivals_map = {'rival1': 'Player One'}

        result = enrich_battle_history(match_history, 'me', rivals_map, include_type=False)

        assert 'type' not in result[0]

    def test_unknown_rival_name(self):
        """Test when rival not in rivals_map."""
        match_history = [{
            'id': 'battle1',
            'user1_id': 'me',
            'user2_id': 'missing_rival',
            'winner_id': 'me',
            'end_date': '2026-02-18',
            'duration': 5
        }]
        rivals_map = {}

        result = enrich_battle_history(match_history, 'me', rivals_map)

        assert result[0]['rival'] == 'Unknown'

    def test_missing_duration_defaults_to_5(self):
        """Test default duration when missing."""
        match_history = [{
            'id': 'battle1',
            'user1_id': 'me',
            'user2_id': 'rival1',
            'winner_id': 'me',
            'end_date': '2026-02-18'
            # No duration field
        }]
        rivals_map = {'rival1': 'Player One'}

        result = enrich_battle_history(match_history, 'me', rivals_map)

        assert result[0]['duration'] == 5

    def test_multiple_battles(self):
        """Test enriching multiple battles."""
        match_history = [
            {
                'id': 'battle1',
                'user1_id': 'me',
                'user2_id': 'rival1',
                'winner_id': 'me',
                'end_date': '2026-02-18',
                'duration': 5
            },
            {
                'id': 'battle2',
                'user1_id': 'rival2',
                'user2_id': 'me',
                'winner_id': 'rival2',
                'end_date': '2026-02-17',
                'duration': 3
            }
        ]
        rivals_map = {'rival1': 'Player One', 'rival2': 'Player Two'}

        result = enrich_battle_history(match_history, 'me', rivals_map)

        assert len(result) == 2
        assert result[0]['result'] == 'WIN'
        assert result[1]['result'] == 'LOSS'

    def test_rival_detection_when_user_is_user2(self):
        """Test rival detection when current user is user2."""
        match_history = [{
            'id': 'battle1',
            'user1_id': 'rival1',
            'user2_id': 'me',
            'winner_id': 'me',
            'end_date': '2026-02-18',
            'duration': 5
        }]
        rivals_map = {'rival1': 'Challenger'}

        result = enrich_battle_history(match_history, 'me', rivals_map)

        assert result[0]['rival'] == 'Challenger'
        assert result[0]['result'] == 'WIN'
