"""
Unit tests for AdventureService.

Tests business logic for adventure operations:
- Tier progression and weighting
- Monster pool generation
- Adventure creation and validation
- Break scheduling
- Damage and XP calculations
"""
import pytest
from datetime import date, timedelta, datetime
from unittest.mock import Mock, patch
from fastapi import HTTPException

from services.adventure_service import AdventureService, TIER_DURATIONS, TIER_MULTIPLIERS


# =============================================================================
# Mock Helpers
# =============================================================================

def create_mock_execute_response(data):
    """Create a mock execute response with data attribute."""
    mock_response = Mock()
    mock_response.data = data
    return mock_response


def setup_profile_mock(mock_supabase, user_id='user-123', **overrides):
    """Setup a profile mock with default values."""
    profile_data = {
        'id': user_id,
        'monster_rating': 0,
        'timezone': 'UTC',
        'monster_pool_refreshes': None,
        'monster_pool_refresh_set_at': None,
    }
    profile_data.update(overrides)

    mock_supabase.table.return_value.select.return_value.eq.return_value.single\
        .return_value.execute.return_value = create_mock_execute_response(profile_data)


# =============================================================================
# Test Tier & Rating Helpers
# =============================================================================

class TestTierHelpers:
    """Test tier progression and weighting logic."""

    def test_get_unlocked_tiers_rating_0(self):
        """Rating 0 unlocks only easy tier."""
        result = AdventureService.get_unlocked_tiers(0)
        assert result == ['easy']

    def test_get_unlocked_tiers_rating_1(self):
        """Rating 1 still only unlocks easy tier."""
        result = AdventureService.get_unlocked_tiers(1)
        assert result == ['easy']

    def test_get_unlocked_tiers_rating_2(self):
        """Rating 2 unlocks easy and medium."""
        result = AdventureService.get_unlocked_tiers(2)
        assert set(result) == {'easy', 'medium'}

    def test_get_unlocked_tiers_rating_5(self):
        """Rating 5 unlocks easy, medium, hard."""
        result = AdventureService.get_unlocked_tiers(5)
        assert set(result) == {'easy', 'medium', 'hard'}

    def test_get_unlocked_tiers_rating_9(self):
        """Rating 9 unlocks easy, medium, hard, expert."""
        result = AdventureService.get_unlocked_tiers(9)
        assert set(result) == {'easy', 'medium', 'hard', 'expert'}

    def test_get_unlocked_tiers_rating_14(self):
        """Rating 14 unlocks all tiers."""
        result = AdventureService.get_unlocked_tiers(14)
        assert set(result) == {'easy', 'medium', 'hard', 'expert', 'boss'}

    def test_get_unlocked_tiers_rating_100(self):
        """Very high rating still unlocks all tiers."""
        result = AdventureService.get_unlocked_tiers(100)
        assert set(result) == {'easy', 'medium', 'hard', 'expert', 'boss'}

    def test_get_tier_weights_rating_0(self):
        """Rating 0 weights easy 100%, others 0%."""
        result = AdventureService.get_tier_weights(0)
        assert result['easy'] == 100
        assert result['medium'] == 0
        assert result['hard'] == 0
        assert result['expert'] == 0
        assert result['boss'] == 0

    def test_get_tier_weights_rating_2(self):
        """Rating 2 weights medium higher."""
        result = AdventureService.get_tier_weights(2)
        assert result['easy'] == 30
        assert result['medium'] == 70
        assert result['hard'] == 0

    def test_get_tier_weights_rating_5(self):
        """Rating 5 weights hard highest."""
        result = AdventureService.get_tier_weights(5)
        assert result['easy'] == 15
        assert result['medium'] == 25
        assert result['hard'] == 60
        assert result['expert'] == 0

    def test_get_tier_weights_rating_9(self):
        """Rating 9 weights expert highest."""
        result = AdventureService.get_tier_weights(9)
        assert result['easy'] == 10
        assert result['medium'] == 15
        assert result['hard'] == 25
        assert result['expert'] == 50
        assert result['boss'] == 0

    def test_get_tier_weights_rating_14(self):
        """Rating 14 includes boss with significant weight."""
        result = AdventureService.get_tier_weights(14)
        assert result['easy'] == 10
        assert result['medium'] == 10
        assert result['hard'] == 15
        assert result['expert'] == 25
        assert result['boss'] == 40


# =============================================================================
# Test Refresh Count Management
# =============================================================================

class TestRefreshCount:
    """Test database-backed refresh count management."""

    @pytest.fixture
    def mock_supabase_base(self):
        with patch('services.adventure_service.supabase') as mock:
            yield mock

    def test_initialize_refresh_count_new_user(self, mock_supabase_base):
        """Initialize refresh count for user with no previous count."""
        setup_profile_mock(
            mock_supabase_base,
            monster_pool_refreshes=None,
            monster_pool_refresh_set_at=None
        )

        result = AdventureService.initialize_refresh_count('user-123')

        assert result == 3
        # Should update profile with new count and timestamp
        mock_supabase_base.table.return_value.update.assert_called_once()

    def test_initialize_refresh_count_existing_today(self, mock_supabase_base):
        """Return existing count if set today."""
        setup_profile_mock(
            mock_supabase_base,
            monster_pool_refreshes=2,
            monster_pool_refresh_set_at=datetime.now().isoformat()
        )

        result = AdventureService.initialize_refresh_count('user-123')

        assert result == 2
        # Should not update
        mock_supabase_base.table.return_value.update.assert_not_called()

    def test_initialize_refresh_count_stale_resets(self, mock_supabase_base):
        """Reset count if timestamp is from yesterday."""
        yesterday = (datetime.now() - timedelta(days=1)).isoformat()
        setup_profile_mock(
            mock_supabase_base,
            monster_pool_refreshes=1,
            monster_pool_refresh_set_at=yesterday
        )

        result = AdventureService.initialize_refresh_count('user-123')

        assert result == 3
        # Should update profile
        mock_supabase_base.table.return_value.update.assert_called_once()

    def test_decrement_refresh_count_success(self, mock_supabase_base):
        """Successfully decrement refresh count."""
        setup_profile_mock(mock_supabase_base, monster_pool_refreshes=3)

        result = AdventureService.decrement_refresh_count('user-123')

        assert result == 2
        mock_supabase_base.table.return_value.update.assert_called_once()

    def test_decrement_refresh_count_exhausted(self, mock_supabase_base):
        """Raise exception when no refreshes remaining."""
        setup_profile_mock(mock_supabase_base, monster_pool_refreshes=0)

        with pytest.raises(HTTPException) as exc_info:
            AdventureService.decrement_refresh_count('user-123')

        assert exc_info.value.status_code == 400
        assert "No refreshes remaining" in exc_info.value.detail

    def test_decrement_refresh_count_none_raises(self, mock_supabase_base):
        """Raise exception when count is None."""
        setup_profile_mock(mock_supabase_base, monster_pool_refreshes=None)

        with pytest.raises(HTTPException) as exc_info:
            AdventureService.decrement_refresh_count('user-123')

        assert exc_info.value.status_code == 400

    def test_reset_refresh_count(self, mock_supabase_base):
        """Reset refresh count to None."""
        setup_profile_mock(mock_supabase_base, monster_pool_refreshes=2)

        AdventureService.reset_refresh_count('user-123')

        # Verify update was called with None values
        call_args = mock_supabase_base.table.return_value.update.call_args[0][0]
        assert call_args['monster_pool_refreshes'] is None
        assert call_args['monster_pool_refresh_set_at'] is None


# =============================================================================
# Test Monster Pool Generation
# =============================================================================

class TestMonsterPool:
    """Test weighted monster pool generation."""

    @pytest.fixture
    def mock_supabase_base(self):
        with patch('services.adventure_service.supabase') as mock:
            yield mock

    def test_get_weighted_monster_pool_returns_4(self, mock_supabase_base):
        """Returns exactly 4 monsters."""
        # Mock monsters from easy tier
        mock_supabase_base.table.return_value.select.return_value.in_.return_value\
            .execute.return_value = create_mock_execute_response([
                {'id': 'm1', 'name': 'Slime', 'tier': 'easy', 'base_hp': 100},
                {'id': 'm2', 'name': 'Rat', 'tier': 'easy', 'base_hp': 120},
                {'id': 'm3', 'name': 'Goblin', 'tier': 'easy', 'base_hp': 150},
                {'id': 'm4', 'name': 'Imp', 'tier': 'easy', 'base_hp': 180},
            ])

        result = AdventureService.get_weighted_monster_pool(0, count=4)

        assert len(result) == 4

    def test_get_weighted_monster_pool_no_duplicates(self, mock_supabase_base):
        """Never returns duplicate monsters."""
        monsters = [
            {'id': f'm{i}', 'name': f'M{i}', 'tier': 'easy', 'base_hp': 100}
            for i in range(10)
        ]
        mock_supabase_base.table.return_value.select.return_value.in_.return_value\
            .execute.return_value = create_mock_execute_response(monsters)

        result = AdventureService.get_weighted_monster_pool(0, count=4)

        ids = [m['id'] for m in result]
        assert len(ids) == len(set(ids)), "No duplicate IDs allowed"

    def test_get_weighted_monster_pool_respects_tier_weights(self, mock_supabase_base):
        """Uses correct weights based on rating."""
        # Rating 5: easy 15%, medium 25%, hard 60%
        monsters = [
            {'id': 'e1', 'name': 'Easy1', 'tier': 'easy', 'base_hp': 100},
            {'id': 'm1', 'name': 'Med1', 'tier': 'medium', 'base_hp': 200},
            {'id': 'm2', 'name': 'Med2', 'tier': 'medium', 'base_hp': 220},
            {'id': 'h1', 'name': 'Hard1', 'tier': 'hard', 'base_hp': 350},
            {'id': 'h2', 'name': 'Hard2', 'tier': 'hard', 'base_hp': 370},
            {'id': 'h3', 'name': 'Hard3', 'tier': 'hard', 'base_hp': 400},
        ]
        mock_supabase_base.table.return_value.select.return_value.in_.return_value\
            .execute.return_value = create_mock_execute_response(monsters)

        result = AdventureService.get_weighted_monster_pool(5, count=4)

        # With rating 5, should get mostly hard monsters
        assert len(result) == 4

    def test_get_weighted_monster_pool_insufficient_monsters(self, mock_supabase_base):
        """Handles case where fewer monsters available than requested."""
        mock_supabase_base.table.return_value.select.return_value.in_.return_value\
            .execute.return_value = create_mock_execute_response([
                {'id': 'm1', 'name': 'Only', 'tier': 'easy', 'base_hp': 100},
            ])

        result = AdventureService.get_weighted_monster_pool(0, count=4)

        # Returns available monsters (less than count)
        assert len(result) < 4

    def test_get_weighted_monster_pool_no_monsters_raises(self, mock_supabase_base):
        """Raises exception when no monsters available."""
        mock_supabase_base.table.return_value.select.return_value.in_.return_value\
            .execute.return_value = create_mock_execute_response([])

        with pytest.raises(HTTPException) as exc_info:
            AdventureService.get_weighted_monster_pool(0)

        assert exc_info.value.status_code == 500
        assert "No monsters available" in exc_info.value.detail


# =============================================================================
# Test Adventure Creation
# =============================================================================

class TestAdventureCreation:
    """Test adventure creation logic."""

    @pytest.fixture
    def mock_supabase_base(self):
        with patch('services.adventure_service.supabase') as mock:
            yield mock

    def test_create_adventure_success(self, mock_supabase_base):
        """Successfully create an adventure."""
        # Mock no active battles
        mock_supabase_base.table.return_value.select.return_value.or_.return_value\
            .in_.return_value.execute.return_value = create_mock_execute_response([])

        # Mock no active adventure
        mock_supabase_base.table.return_value.select.return_value.eq.return_value.eq\
            .return_value.execute.return_value = create_mock_execute_response([])

        # Mock monster fetch (first select().eq().single() call on monsters table)
        # Mock profile fetch (second select().eq().single() call on profiles table)
        # Need to track call order by setting up different mock chains

        # Setup separate call chain for monsters table
        mock_supabase_base.table.return_value.select.return_value.eq.return_value.single\
            .return_value.execute.side_effect = [
                create_mock_execute_response({
                    'id': 'monster-1',
                    'name': 'Slime',
                    'tier': 'easy',
                    'base_hp': 100
                }),
                create_mock_execute_response({'monster_rating': 0}),
            ]

        # Mock adventure insert
        mock_supabase_base.table.return_value.insert.return_value.execute\
            .return_value = create_mock_execute_response([{
                'id': 'adv-123',
                'user_id': 'user-123',
                'monster_id': 'monster-1',
                'status': 'active'
            }])

        result = AdventureService.create_adventure('user-123', 'monster-1')

        assert result['id'] == 'adv-123'
        assert result['status'] == 'active'

    def test_create_adventure_active_battle_raises(self, mock_supabase_base):
        """Raise exception when user has active battle."""
        mock_supabase_base.table.return_value.select.return_value.or_.return_value\
            .in_.return_value.execute.return_value = create_mock_execute_response([
            {'id': 'battle-1'}
        ])

        with pytest.raises(HTTPException) as exc_info:
            AdventureService.create_adventure('user-123', 'monster-1')

        assert exc_info.value.status_code == 400
        assert "active battle" in exc_info.value.detail

    def test_create_adventure_active_adventure_raises(self, mock_supabase_base):
        """Raise exception when user has active adventure."""
        # Mock no active battles
        mock_supabase_base.table.return_value.select.return_value.or_.return_value\
            .in_.return_value.execute.return_value = create_mock_execute_response([])

        # Mock existing adventure
        mock_supabase_base.table.return_value.select.return_value.eq.return_value.eq\
            .return_value.execute.return_value = create_mock_execute_response([
            {'id': 'adv-1'}
        ])

        with pytest.raises(HTTPException) as exc_info:
            AdventureService.create_adventure('user-123', 'monster-1')

        assert exc_info.value.status_code == 400
        assert "active adventure" in exc_info.value.detail

    def test_create_adventure_monster_not_found_raises(self, mock_supabase_base):
        """Raise exception when monster doesn't exist."""
        # Mock no active sessions
        mock_supabase_base.table.return_value.select.return_value.or_.return_value\
            .in_.return_value.execute.return_value = create_mock_execute_response([])
        mock_supabase_base.table.return_value.select.return_value.eq.return_value.eq\
            .return_value.execute.return_value = create_mock_execute_response([])

        # Mock profile
        mock_supabase_base.table.return_value.select.return_value.eq.return_value.single\
            .return_value.execute.return_value = create_mock_execute_response({
                'monster_rating': 0
            })

        # Mock monster not found
        mock_supabase_base.table.return_value.select.return_value.eq.return_value.single\
            .return_value.execute.side_effect = Exception("Not found")

        with pytest.raises(HTTPException) as exc_info:
            AdventureService.create_adventure('user-123', 'monster-1')

        assert exc_info.value.status_code == 404

    def test_create_adventure_tier_locked_raises(self, mock_supabase_base):
        """Raise exception when monster tier is locked."""
        # Mock no active sessions
        mock_supabase_base.table.return_value.select.return_value.or_.return_value\
            .in_.return_value.execute.return_value = create_mock_execute_response([])
        mock_supabase_base.table.return_value.select.return_value.eq.return_value.eq\
            .return_value.execute.return_value = create_mock_execute_response([])

        # Mock monster with hard tier (locked) - comes first
        # Mock profile with rating 0 (only easy unlocked) - comes second
        mock_supabase_base.table.return_value.select.return_value.eq.return_value.single\
            .return_value.execute.side_effect = [
                create_mock_execute_response({
                    'id': 'monster-1',
                    'tier': 'hard',
                    'base_hp': 400
                }),
                create_mock_execute_response({'monster_rating': 0}),
            ]

        with pytest.raises(HTTPException) as exc_info:
            AdventureService.create_adventure('user-123', 'monster-1')

        assert exc_info.value.status_code == 403
        assert "not unlocked" in exc_info.value.detail


# =============================================================================
# Test Break Scheduling
# =============================================================================

class TestBreakScheduling:
    """Test break day scheduling."""

    @pytest.fixture
    def mock_supabase_base(self):
        with patch('services.adventure_service.supabase') as mock:
            yield mock

    def test_schedule_break_success(self, mock_supabase_base):
        """Successfully schedule a break day."""
        adventure = {
            'id': 'adv-123',
            'user_id': 'user-123',
            'status': 'active',
            'deadline': (date.today() + timedelta(days=3)).isoformat(),
            'break_days_used': 0,
            'max_break_days': 2,
            'is_on_break': False,
        }

        mock_supabase_base.table.return_value.select.return_value.eq.return_value.single\
            .return_value.execute.return_value = create_mock_execute_response(adventure)

        result = AdventureService.schedule_break('adv-123', 'user-123')

        assert result['status'] == 'break_scheduled'
        assert result['breaks_remaining'] == 1  # 2 - 0 - 1

    def test_schedule_break_not_found_raises(self, mock_supabase_base):
        """Raise exception when adventure not found."""
        mock_supabase_base.table.return_value.select.return_value.eq.return_value.single\
            .return_value.execute.return_value = create_mock_execute_response(None)

        with pytest.raises(HTTPException) as exc_info:
            AdventureService.schedule_break('adv-123', 'user-123')

        assert exc_info.value.status_code == 404

    def test_schedule_break_not_owner_raises(self, mock_supabase_base):
        """Raise exception when user doesn't own adventure."""
        adventure = {
            'id': 'adv-123',
            'user_id': 'other-user',  # Different user
            'status': 'active',
            'deadline': (date.today() + timedelta(days=3)).isoformat(),
            'break_days_used': 0,
            'max_break_days': 2,
            'is_on_break': False,
        }

        mock_supabase_base.table.return_value.select.return_value.eq.return_value.single\
            .return_value.execute.return_value = create_mock_execute_response(adventure)

        with pytest.raises(HTTPException) as exc_info:
            AdventureService.schedule_break('adv-123', 'user-123')

        assert exc_info.value.status_code == 403
        assert "Not your adventure" in exc_info.value.detail

    def test_schedule_break_no_breaks_remaining(self, mock_supabase_base):
        """Raise exception when no break days remaining."""
        adventure = {
            'id': 'adv-123',
            'user_id': 'user-123',
            'status': 'active',
            'deadline': (date.today() + timedelta(days=3)).isoformat(),
            'break_days_used': 2,  # Already used both
            'max_break_days': 2,
            'is_on_break': False,
        }

        mock_supabase_base.table.return_value.select.return_value.eq.return_value.single\
            .return_value.execute.return_value = create_mock_execute_response(adventure)

        with pytest.raises(HTTPException) as exc_info:
            AdventureService.schedule_break('adv-123', 'user-123')

        assert exc_info.value.status_code == 400
        assert "No break days remaining" in exc_info.value.detail

    def test_schedule_break_already_on_break(self, mock_supabase_base):
        """Raise exception when already on break."""
        adventure = {
            'id': 'adv-123',
            'user_id': 'user-123',
            'status': 'active',
            'deadline': (date.today() + timedelta(days=3)).isoformat(),
            'break_days_used': 0,
            'max_break_days': 2,
            'is_on_break': True,  # Already on break
        }

        mock_supabase_base.table.return_value.select.return_value.eq.return_value.single\
            .return_value.execute.return_value = create_mock_execute_response(adventure)

        with pytest.raises(HTTPException) as exc_info:
            AdventureService.schedule_break('adv-123', 'user-123')

        assert exc_info.value.status_code == 400
        assert "Already on break" in exc_info.value.detail


# =============================================================================
# Test Damage & XP Calculations
# =============================================================================

class TestCalculations:
    """Test damage and XP calculation formulas."""

    def test_calculate_damage_all_mandatory(self):
        """Full damage when all mandatory tasks completed."""
        result = AdventureService.calculate_damage(5, 5, 0)
        assert result == 100  # 5/5 * 100 + 0

    def test_calculate_damage_half_mandatory(self):
        """Half damage when half mandatory tasks completed."""
        result = AdventureService.calculate_damage(3, 6, 0)
        assert result == 50  # 3/6 * 100 + 0

    def test_calculate_damage_with_optional(self):
        """Bonus damage from optional tasks."""
        result = AdventureService.calculate_damage(5, 5, 2)
        assert result == 120  # 100 + 2*10, capped at 120

    def test_calculate_damage_capped_at_120(self):
        """Damage never exceeds 120."""
        result = AdventureService.calculate_damage(5, 5, 5)
        assert result == 120  # 100 + 50 = 150, capped at 120

    def test_calculate_damage_no_mandatory_only_optional(self):
        """Only optional tasks completed."""
        result = AdventureService.calculate_damage(0, 0, 3)
        assert result == 30  # 0 + 3*10

    def test_calculate_damage_none_completed(self):
        """Zero damage when nothing completed."""
        result = AdventureService.calculate_damage(0, 5, 0)
        assert result == 0

    def test_calculate_adventure_xp_easy_victory(self):
        """Easy tier victory multiplier."""
        result = AdventureService.calculate_adventure_xp(400, 'easy', True)
        assert result == 400  # 400 * 1.0 * 1.0

    def test_calculate_adventure_xp_medium_victory(self):
        """Medium tier victory multiplier."""
        result = AdventureService.calculate_adventure_xp(400, 'medium', True)
        assert result == 480  # 400 * 1.2 * 1.0

    def test_calculate_adventure_xp_hard_victory(self):
        """Hard tier victory multiplier."""
        result = AdventureService.calculate_adventure_xp(400, 'hard', True)
        assert result == 600  # 400 * 1.5 * 1.0

    def test_calculate_adventure_xp_expert_victory(self):
        """Expert tier victory multiplier."""
        result = AdventureService.calculate_adventure_xp(400, 'expert', True)
        assert result == 800  # 400 * 2.0 * 1.0

    def test_calculate_adventure_xp_boss_victory(self):
        """Boss tier victory multiplier."""
        result = AdventureService.calculate_adventure_xp(400, 'boss', True)
        assert result == 1200  # 400 * 3.0 * 1.0

    def test_calculate_adventure_xp_escape_half(self):
        """Escape grants 50% XP."""
        result = AdventureService.calculate_adventure_xp(400, 'medium', False)
        assert result == 240  # 400 * 1.2 * 0.5

    def test_calculate_adventure_xp_abandon_half(self):
        """Abandon grants 50% XP."""
        result = AdventureService.calculate_adventure_xp(300, 'hard', False)
        assert result == 225  # 300 * 1.5 * 0.5


# =============================================================================
# Test Tier Constants
# =============================================================================

class TestTierConstants:
    """Verify tier configuration constants."""

    def test_tier_durations(self):
        """TIER_DURATIONS has all expected tiers."""
        assert 'easy' in TIER_DURATIONS
        assert 'medium' in TIER_DURATIONS
        assert 'hard' in TIER_DURATIONS
        assert 'expert' in TIER_DURATIONS
        assert 'boss' in TIER_DURATIONS

    def test_tier_multipliers(self):
        """TIER_MULTIPLIERS has all expected tiers."""
        assert 'easy' in TIER_MULTIPLIERS
        assert 'medium' in TIER_MULTIPLIERS
        assert 'hard' in TIER_MULTIPLIERS
        assert 'expert' in TIER_MULTIPLIERS
        assert 'boss' in TIER_MULTIPLIERS

    def test_multiplier_values(self):
        """Multipliers increase with tier."""
        assert TIER_MULTIPLIERS['easy'] == 1.0
        assert TIER_MULTIPLIERS['medium'] == 1.2
        assert TIER_MULTIPLIERS['hard'] == 1.5
        assert TIER_MULTIPLIERS['expert'] == 2.0
        assert TIER_MULTIPLIERS['boss'] == 3.0
