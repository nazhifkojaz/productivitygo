"""
Battle helper functions for routers.

This module contains pure helper functions extracted from the battles router
to improve testability and maintainability.

REFACTOR-005: Phase 5 - Item 6.1
"""
from typing import Dict, Tuple
from datetime import date

from utils.stats import format_win_rate
from utils.logging_config import get_logger

logger = get_logger(__name__)


# Default profile values for null profiles
DEFAULT_USER_PROFILE = {
    'timezone': 'UTC',
    'username': 'Unknown',
    'level': 1
}

DEFAULT_RIVAL_PROFILE = {
    'timezone': 'UTC',
    'username': 'Unknown Rival',
    'level': 1,
    'battle_win_count': 0,
    'battle_count': 0,
    'total_xp_earned': 0,
    'completed_tasks': 0
}


def extract_user_profiles(battle: Dict, user_id: str) -> Tuple[Dict, Dict, str]:
    """
    Extract user and rival profiles from battle, handling null profiles.

    Args:
        battle: Battle dict with embedded user1/user2 profiles
        user_id: The current user's ID

    Returns:
        Tuple of (user_profile, rival_profile, rival_id)

    Side Effects:
        Logs warning if profiles are missing
    """
    if battle['user1_id'] == user_id:
        user_profile = battle['user1']
        rival_profile = battle['user2']
        rival_id = battle['user2_id']
    else:
        user_profile = battle['user2']
        rival_profile = battle['user1']
        rival_id = battle['user1_id']

    # Handle None profiles with defaults
    if user_profile is None:
        logger.warning(f"User profile missing for battle {battle['id']}, user {user_id}")
        user_profile = DEFAULT_USER_PROFILE.copy()

    if rival_profile is None:
        logger.warning(f"Rival profile missing for battle {battle['id']}, rival {rival_id}")
        rival_profile = DEFAULT_RIVAL_PROFILE.copy()

    return user_profile, rival_profile, rival_id


def calculate_app_state(
    battle_status: str,
    start_date: date,
    end_date: date,
    user_today: date
) -> str:
    """
    Calculate app state based on dates and battle status.

    Args:
        battle_status: Current battle status ('pending', 'active', 'completed')
        start_date: Battle start date
        end_date: Battle end date
        user_today: Today's date in user's timezone

    Returns:
        App state string: PENDING_ACCEPTANCE, PRE_BATTLE, IN_BATTLE,
        LAST_BATTLE_DAY, or BATTLE_END
    """
    if battle_status == 'pending':
        return 'PENDING_ACCEPTANCE'

    if battle_status == 'completed':
        return 'BATTLE_END'

    if user_today < start_date:
        return 'PRE_BATTLE'

    if user_today > end_date:
        return 'BATTLE_END'

    # We're in the battle range
    if user_today == end_date:
        return 'LAST_BATTLE_DAY'

    return 'IN_BATTLE'


def build_rival_intelligence(
    rival_profile: Dict,
    total_tasks: int = 0,
    completed_tasks: int = 0
) -> Dict:
    """
    Build rival intelligence dict for frontend.

    Args:
        rival_profile: Rival's profile data
        total_tasks: Total tasks for today (default 0)
        completed_tasks: Completed tasks for today (default 0)

    Returns:
        Rival intelligence dict with username, level, tasks, and stats
    """
    battle_win_count = rival_profile.get('battle_win_count', 0)
    battle_count = rival_profile.get('battle_count', 0)

    return {
        'username': rival_profile.get('username', 'Unknown Rival'),
        'level': rival_profile.get('level', 1),
        'tasks_total': total_tasks,
        'tasks_completed': completed_tasks,
        'stats': {
            'battle_wins': battle_win_count,
            'battle_fought': battle_count,
            'level': rival_profile.get('level', 1),
            'total_xp': rival_profile.get('total_xp_earned', 0),
            'win_rate': format_win_rate(battle_win_count, battle_count),
            'tasks_completed': rival_profile.get('completed_tasks', 0)
        }
    }
