"""
Battle query service for database operations.

This service layer separates query logic from the router layer,
making it testable and reusable across different endpoints.

REFACTOR-005: Phase 5 - Item 6.1
"""
from typing import Dict, Optional, Tuple
from datetime import date

from database import supabase
from utils.query_columns import BATTLE_RELOAD
from utils.logging_config import get_logger

logger = get_logger(__name__)


class BattleQueryService:
    """
    Service layer for battle query operations.

    Separates query logic from router layer, making it testable
    and reusable across different endpoints.
    """

    @staticmethod
    async def fetch_active_battle_with_profiles(user_id: str) -> Optional[Dict]:
        """
        Fetch the most relevant active battle for a user with embedded profiles.

        Args:
            user_id: The user's ID

        Returns:
            Battle dict with embedded user1/user2 profiles, or None if no active battle

        Raises:
            Exception: If database query fails
        """
        BATTLE_WITH_PROFILES_QUERY = (
            "*, "
            "user1:profiles!user1_id(username, level, timezone, battle_win_count, "
            "battle_count, total_xp_earned, completed_tasks), "
            "user2:profiles!user2_id(username, level, timezone, battle_win_count, "
            "battle_count, total_xp_earned, completed_tasks)"
        )

        res = await supabase.table("battles").select(BATTLE_WITH_PROFILES_QUERY)\
            .or_(f"user1_id.eq.{user_id},user2_id.eq.{user_id}")\
            .eq("status", "active")\
            .execute()

        if not res.data:
            return None

        # Return most relevant battle (latest ending)
        return max(res.data, key=lambda b: b['end_date'])

    @staticmethod
    async def calculate_rounds_played(battle_id: str, user_id: str) -> int:
        """
        Calculate how many rounds a user has played in a battle.

        Args:
            battle_id: The battle ID
            user_id: The user's ID

        Returns:
            Number of daily entries submitted by the user
        """
        rounds_res = await supabase.table("daily_entries").select("id")\
            .eq("battle_id", battle_id)\
            .eq("user_id", user_id)\
            .execute()

        return len(rounds_res.data)

    @staticmethod
    async def fetch_rival_tasks_for_today(rival_id: str, today_str: str) -> Tuple[int, int]:
        """
        Fetch rival's task completion for today.

        Args:
            rival_id: The rival's user ID
            today_str: Today's date in ISO format

        Returns:
            Tuple of (total_tasks, completed_tasks)
        """
        # Get Daily Entry
        rival_entry_res = await supabase.table("daily_entries").select("id")\
            .eq("user_id", rival_id)\
            .eq("date", today_str)\
            .execute()

        if not rival_entry_res.data:
            return (0, 0)

        entry_id = rival_entry_res.data[0]['id']

        # Get Tasks
        rival_tasks_res = await supabase.table("tasks").select("is_completed")\
            .eq("daily_entry_id", entry_id)\
            .execute()

        rival_tasks = rival_tasks_res.data
        total_tasks = len(rival_tasks)
        completed_tasks = sum(1 for t in rival_tasks if t['is_completed'])

        return (total_tasks, completed_tasks)

    @staticmethod
    async def reload_battle_state(battle_id: str) -> Optional[Dict]:
        """
        Reload battle state after lazy evaluation.

        Args:
            battle_id: The battle ID

        Returns:
            Updated battle fields (status, current_round) or None
        """
        battle_reload = await supabase.table("battles").select(BATTLE_RELOAD)\
            .eq("id", battle_id)\
            .single()\
            .execute()

        return battle_reload.data if battle_reload.data else None
