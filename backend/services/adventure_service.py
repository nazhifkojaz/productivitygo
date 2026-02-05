"""
Adventure Mode Service Layer

Handles business logic for adventure operations:
- Monster pool generation with tier weighting
- Adventure creation and validation
- Break scheduling
- Damage and XP calculations
"""

from datetime import date, timedelta, datetime
import random
from typing import List, Dict
from fastapi import HTTPException
from database import supabase
from utils.logging_config import get_logger

logger = get_logger(__name__)

# =============================================================================
# Constants
# =============================================================================

TIER_DURATIONS = {
    'easy': (3, 4),
    'medium': (4, 5),
    'hard': (5, 6),
    'expert': (5, 7),
    'boss': (5, 7),
}

TIER_MULTIPLIERS = {
    'easy': 1.0,
    'medium': 1.2,
    'hard': 1.5,
    'expert': 2.0,
    'boss': 3.0,
}

TIER_THRESHOLDS = {
    0: ['easy'],
    2: ['easy', 'medium'],
    5: ['easy', 'medium', 'hard'],
    9: ['easy', 'medium', 'hard', 'expert'],
    14: ['easy', 'medium', 'hard', 'expert', 'boss'],
}

TIER_WEIGHTS = {
    # rating_threshold: {tier: weight}
    0: {'easy': 100, 'medium': 0, 'hard': 0, 'expert': 0, 'boss': 0},
    2: {'easy': 30, 'medium': 70, 'hard': 0, 'expert': 0, 'boss': 0},
    5: {'easy': 15, 'medium': 25, 'hard': 60, 'expert': 0, 'boss': 0},
    9: {'easy': 10, 'medium': 15, 'hard': 25, 'expert': 50, 'boss': 0},
    14: {'easy': 10, 'medium': 10, 'hard': 15, 'expert': 25, 'boss': 40},
}


class AdventureService:
    """Service class for adventure operations."""

    # =========================================================================
    # Tier & Rating Helpers
    # =========================================================================

    @staticmethod
    def get_unlocked_tiers(rating: int) -> List[str]:
        """Get list of unlocked tiers based on monster rating."""
        for threshold in sorted(TIER_THRESHOLDS.keys(), reverse=True):
            if rating >= threshold:
                return TIER_THRESHOLDS[threshold]
        return ['easy']

    @staticmethod
    def get_tier_weights(rating: int) -> Dict[str, int]:
        """Get tier weights for monster pool based on rating."""
        for threshold in sorted(TIER_WEIGHTS.keys(), reverse=True):
            if rating >= threshold:
                return TIER_WEIGHTS[threshold]
        return TIER_WEIGHTS[0]

    # =========================================================================
    # Refresh Tracking (Database-backed, Redis-free)
    # =========================================================================

    @staticmethod
    def initialize_refresh_count(user_id: str) -> int:
        """
        Initialize or refresh the monster pool refresh count.
        Resets to 3 if not set today, otherwise returns current count.

        Returns:
            Current refresh count (always starts at 3 for new session)
        """
        profile_res = supabase.table("profiles").select(
            "monster_pool_refreshes", "monster_pool_refresh_set_at"
        ).eq("id", user_id).single().execute()

        if not profile_res.data:
            raise HTTPException(status_code=404, detail="Profile not found")

        profile = profile_res.data
        refreshes = profile.get('monster_pool_refreshes')
        set_at = profile.get('monster_pool_refresh_set_at')

        # Check if we need to reset (not set today)
        should_reset = True
        if set_at and refreshes is not None:
            try:
                set_at_date = datetime.fromisoformat(set_at.replace('Z', '+00:00')).date()
                if set_at_date == date.today():
                    should_reset = False
            except (ValueError, AttributeError):
                should_reset = True

        if should_reset:
            # Reset to 3 and update timestamp
            supabase.table("profiles").update({
                "monster_pool_refreshes": 3,
                "monster_pool_refresh_set_at": datetime.utcnow().isoformat()
            }).eq("id", user_id).execute()
            return 3
        else:
            # Return existing count
            return refreshes if refreshes is not None else 3

    @staticmethod
    def decrement_refresh_count(user_id: str) -> int:
        """
        Decrement the refresh count by 1.

        Returns:
            New refresh count after decrement

        Raises:
            HTTPException: If no refreshes remaining
        """
        profile_res = supabase.table("profiles").select(
            "monster_pool_refreshes"
        ).eq("id", user_id).single().execute()

        if not profile_res.data:
            raise HTTPException(status_code=404, detail="Profile not found")

        current = profile_res.data.get('monster_pool_refreshes')

        if current is None or current <= 0:
            raise HTTPException(status_code=400, detail="No refreshes remaining")

        new_count = current - 1
        supabase.table("profiles").update({
            "monster_pool_refreshes": new_count
        }).eq("id", user_id).execute()

        return new_count

    @staticmethod
    def reset_refresh_count(user_id: str):
        """
        Reset the refresh count to NULL after adventure starts.
        This allows a fresh count for the next adventure.
        """
        supabase.table("profiles").update({
            "monster_pool_refreshes": None,
            "monster_pool_refresh_set_at": None
        }).eq("id", user_id).execute()

    # =========================================================================
    # Monster Pool
    # =========================================================================

    @staticmethod
    def get_weighted_monster_pool(rating: int, count: int = 4) -> List[dict]:
        """
        Get weighted random monster pool based on rating.

        Args:
            rating: User's monster rating
            count: Number of monsters to return (default 4)

        Returns:
            List of monster dicts
        """
        unlocked_tiers = AdventureService.get_unlocked_tiers(rating)
        weights = AdventureService.get_tier_weights(rating)

        # Fetch all monsters from unlocked tiers
        monsters_res = supabase.table("monsters").select("*")\
            .in_("tier", unlocked_tiers).execute()

        if not monsters_res.data:
            raise HTTPException(status_code=500, detail="No monsters available")

        all_monsters = monsters_res.data

        # Weighted random selection without replacement
        pool = []
        selected_ids = set()

        for _ in range(count):
            # Filter out already selected monsters
            available = [m for m in all_monsters if m['id'] not in selected_ids]
            if not available:
                break

            # Build weighted list
            weighted_list = []
            for monster in available:
                weight = weights.get(monster['tier'], 0)
                if weight > 0:
                    weighted_list.extend([monster] * weight)

            if not weighted_list:
                break

            # Select random monster
            selected = random.choice(weighted_list)
            pool.append(selected)
            selected_ids.add(selected['id'])

        return pool

    # =========================================================================
    # Adventure Creation
    # =========================================================================

    @staticmethod
    def create_adventure(user_id: str, monster_id: str) -> dict:
        """
        Create a new adventure.

        Args:
            user_id: User's UUID
            monster_id: Selected monster's UUID

        Returns:
            Created adventure dict

        Raises:
            HTTPException: If user has active session or monster not found
        """
        # 1. Check for active battle
        existing_battle = supabase.table("battles").select("id")\
            .or_(f"user1_id.eq.{user_id},user2_id.eq.{user_id}")\
            .in_("status", ["active", "pending"]).execute()

        if existing_battle.data:
            raise HTTPException(
                status_code=400,
                detail="You already have an active battle. Complete or forfeit it first."
            )

        # 2. Check for active adventure
        existing_adventure = supabase.table("adventures").select("id")\
            .eq("user_id", user_id).eq("status", "active").execute()

        if existing_adventure.data:
            raise HTTPException(
                status_code=400,
                detail="You already have an active adventure."
            )

        # 3. Fetch monster
        try:
            monster_res = supabase.table("monsters").select("*")\
                .eq("id", monster_id).single().execute()
        except Exception:
            raise HTTPException(status_code=404, detail="Monster not found")

        if not monster_res.data:
            raise HTTPException(status_code=404, detail="Monster not found")

        monster = monster_res.data

        # 4. Check tier access
        profile_res = supabase.table("profiles").select("monster_rating")\
            .eq("id", user_id).single().execute()

        if not profile_res.data:
            raise HTTPException(status_code=404, detail="Profile not found")

        rating = profile_res.data.get('monster_rating', 0)
        unlocked_tiers = AdventureService.get_unlocked_tiers(rating)

        if monster['tier'] not in unlocked_tiers:
            raise HTTPException(
                status_code=403,
                detail=f"Tier '{monster['tier']}' is not unlocked. Rating: {rating}"
            )

        # 5. Generate duration based on tier
        min_dur, max_dur = TIER_DURATIONS.get(monster['tier'], (3, 5))
        duration = random.randint(min_dur, max_dur)

        # 6. Create adventure
        start_date_val = date.today()
        deadline_val = start_date_val + timedelta(days=duration - 1)

        adventure_data = {
            "user_id": user_id,
            "monster_id": monster_id,
            "duration": duration,
            "start_date": start_date_val.isoformat(),
            "deadline": deadline_val.isoformat(),
            "monster_max_hp": monster['base_hp'],
            "monster_current_hp": monster['base_hp'],
            "status": "active",
            "current_round": 0,
            "total_damage_dealt": 0,
            "break_days_used": 0,
            "max_break_days": 2,
        }

        res = supabase.table("adventures").insert(adventure_data).execute()

        if not res.data:
            raise HTTPException(status_code=500, detail="Failed to create adventure")

        adventure = res.data[0]

        # 7. Update profile with current_adventure and reset refresh count
        supabase.table("profiles").update({
            "current_adventure": adventure['id'],
            "monster_pool_refreshes": None,
            "monster_pool_refresh_set_at": None
        }).eq("id", user_id).execute()

        logger.info(f"Adventure created: {adventure['id']} for user {user_id}")

        return adventure

    # =========================================================================
    # Break Scheduling
    # =========================================================================

    @staticmethod
    def schedule_break(adventure_id: str, user_id: str) -> dict:
        """
        Schedule tomorrow as a break day.

        Args:
            adventure_id: Adventure UUID
            user_id: User UUID for verification

        Returns:
            Status dict with break date

        Raises:
            HTTPException: If adventure not found, not owned, or no breaks left
        """
        # 1. Fetch adventure
        adventure_res = supabase.table("adventures").select("*")\
            .eq("id", adventure_id).single().execute()

        if not adventure_res.data:
            raise HTTPException(status_code=404, detail="Adventure not found")

        adventure = adventure_res.data

        # 2. Verify ownership
        if adventure['user_id'] != user_id:
            raise HTTPException(status_code=403, detail="Not your adventure")

        # 3. Check status
        if adventure['status'] != 'active':
            raise HTTPException(status_code=400, detail="Adventure is not active")

        # 4. Check break availability
        if adventure['break_days_used'] >= adventure['max_break_days']:
            raise HTTPException(status_code=400, detail="No break days remaining")

        if adventure['is_on_break']:
            raise HTTPException(status_code=400, detail="Already on break")

        # 5. Schedule break for tomorrow
        tomorrow = date.today() + timedelta(days=1)
        current_deadline = date.fromisoformat(adventure['deadline'])
        new_deadline = current_deadline + timedelta(days=1)

        supabase.table("adventures").update({
            "is_on_break": True,
            "break_end_date": tomorrow.isoformat(),
            "break_days_used": adventure['break_days_used'] + 1,
            "deadline": new_deadline.isoformat(),
        }).eq("id", adventure_id).execute()

        logger.info(f"Break scheduled for adventure {adventure_id} on {tomorrow}")

        return {
            "status": "break_scheduled",
            "break_date": tomorrow.isoformat(),
            "new_deadline": new_deadline.isoformat(),
            "breaks_remaining": adventure['max_break_days'] - adventure['break_days_used'] - 1
        }

    # =========================================================================
    # Adventure Completion
    # =========================================================================

    @staticmethod
    def abandon_adventure(adventure_id: str, user_id: str) -> dict:
        """
        Abandon adventure early with 50% XP.

        Uses SQL function for atomic operation.
        """
        try:
            result = supabase.rpc("abandon_adventure", {
                "adventure_uuid": adventure_id,
                "abandoning_user": user_id
            }).execute()

            if result.data:
                data = result.data[0] if isinstance(result.data, list) else result.data
                logger.info(f"Adventure {adventure_id} abandoned by {user_id}")
                return {
                    "status": data.get('status'),
                    "xp_earned": data.get('xp_earned')
                }
            else:
                raise HTTPException(status_code=500, detail="Failed to abandon adventure")

        except Exception as e:
            error_str = str(e).lower()
            if 'not found' in error_str:
                raise HTTPException(status_code=404, detail="Adventure not found")
            elif 'not your adventure' in error_str:
                raise HTTPException(status_code=403, detail="Not your adventure")
            elif 'not active' in error_str:
                raise HTTPException(status_code=400, detail="Adventure is not active")
            else:
                raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

    # =========================================================================
    # Damage & XP Calculations
    # =========================================================================

    @staticmethod
    def calculate_damage(mandatory_completed: int, mandatory_total: int, optional_completed: int) -> int:
        """
        Calculate daily damage dealt to monster.

        Formula: (mandatory_completed / mandatory_total) * 100 + (optional_completed * 10)
        Max: 120
        """
        if mandatory_total > 0:
            base_damage = int((mandatory_completed / mandatory_total) * 100)
        else:
            base_damage = 0

        bonus_damage = optional_completed * 10
        return min(base_damage + bonus_damage, 120)

    @staticmethod
    def calculate_adventure_xp(total_damage: int, tier: str, is_victory: bool) -> int:
        """
        Calculate XP reward for adventure.

        Formula: total_damage * tier_multiplier * outcome_multiplier
        """
        multiplier = TIER_MULTIPLIERS.get(tier, 1.0)
        outcome_multiplier = 1.0 if is_victory else 0.5
        return int(total_damage * multiplier * outcome_multiplier)
