"""
User Profile Response Builders

Centralized utilities for building user profile responses and
enriching battle history with rival information.

REFACTOR-007: Extracted from routers/social.py (3x duplication)
and routers/users.py (2x similar implementations) to eliminate
duplicate code and ensure consistent API responses.
"""
from typing import List, Dict, Any
from database import supabase
from utils.rank_calculations import calculate_rank


def build_user_profiles_list(profiles_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Build a list of standardized user profile responses.

    Used by social endpoints (following, followers, search) to ensure
    consistent profile formatting across the API. This replaces 3
    identical loops that were previously in social.py.

    Args:
        profiles_data: List of raw profile dicts from database.
                      Must contain: id
                      Optional: username, level, battle_count, battle_win_count, avatar_emoji

    Returns:
        List of standardized profile dicts with keys:
        - id: str
        - username: str (default 'Unknown')
        - level: int (default 1)
        - rank: str (calculated via calculate_rank())
        - avatar_url: None (reserved for future use)
        - avatar_emoji: str (default '😀')

    Examples:
        >>> profiles = [
        ...     {'id': 'abc', 'username': 'player1', 'level': 5,
        ...      'battle_count': 10, 'battle_win_count': 6, 'avatar_emoji': '😀'}
        ... ]
        >>> build_user_profiles_list(profiles)
        [{'id': 'abc', 'username': 'player1', 'level': 5, 'rank': 'Challenger',
          'avatar_url': None, 'avatar_emoji': '😀'}]

    Used By:
        - routers.social.get_following() (replaces lines 70-80)
        - routers.social.get_followers() (replaces lines 106-116)
        - routers.social.search_users() (replaces lines 139-149)

    Edge Cases:
        - Empty list returns empty list
        - Missing fields fall back to defaults
    """
    result = []
    for profile in profiles_data:
        level = profile.get('level') or 1
        result.append({
            'id': profile['id'],
            'username': profile.get('username', 'Unknown'),
            'level': level,
            'rank': calculate_rank(
                level,
                profile.get('battle_count', 0),
                profile.get('battle_win_count', 0)
            ),
            'avatar_url': None,
            'avatar_emoji': profile.get('avatar_emoji', '😀')
        })
    return result


async def batch_fetch_rival_usernames(
    match_history: List[Dict[str, Any]],
    user_id: str
) -> Dict[str, str]:
    """
    Collect rival IDs from match history and batch-fetch their usernames.

    Solves the N+1 query problem by fetching all rival profiles in a
    single database query instead of one query per battle.

    Args:
        match_history: List of battle dicts with user1_id and user2_id
        user_id: Current user's ID (to identify rival in each battle)

    Returns:
        Dict mapping rival_id -> rival_username.
        Returns empty dict if match_history is empty.

    Examples:
        >>> history = [
        ...     {'user1_id': 'user1', 'user2_id': 'rival1'},
        ...     {'user1_id': 'rival2', 'user2_id': 'user1'}
        ... ]
        >>> await batch_fetch_rival_usernames(history, 'user1')
        {'rival1': 'Player One', 'rival2': 'Player Two'}

    Used By:
        - routers.users.get_profile() (replaces lines 120-130)
        - routers.users.get_public_profile() (replaces lines 323-333)

    Performance:
        - O(n) for ID collection where n = number of battles
        - Single IN query for profile fetch
        - Avoids N+1 query pattern
    """
    # Collect unique rival IDs
    rival_ids = set()
    for battle in match_history:
        rival_id = battle['user2_id'] if battle['user1_id'] == user_id else battle['user1_id']
        rival_ids.add(rival_id)

    if not rival_ids:
        return {}

    # Batch fetch all rival profiles
    rivals_res = await supabase.table("profiles")\
        .select("id, username")\
        .in_("id", list(rival_ids))\
        .execute()

    return {r['id']: r['username'] for r in rivals_res.data}


def enrich_battle_history(
    match_history: List[Dict[str, Any]],
    user_id: str,
    rivals_map: Dict[str, str],
    include_type: bool = False
) -> List[Dict[str, Any]]:
    """
    Enrich raw battle rows with rival names and result labels.

    Transforms database battle rows into frontend-ready match history
    entries with human-readable results and rival information.

    Args:
        match_history: List of battle dicts from database.
                      Must contain: id, user1_id, user2_id, end_date
                      Optional: winner_id, duration
        user_id: Current user's ID (for result calculation)
        rivals_map: Dict mapping rival_id -> username
                   (from batch_fetch_rival_usernames)
        include_type: If True, adds 'type' field for battle/adventure distinction.
                     Private profile uses True (combines battles + adventures).
                     Public profile uses False (battles only).

    Returns:
        List of enriched match history entries with keys:
        - id: str (battle ID)
        - date: str (end_date ISO string)
        - rival: str (rival username)
        - result: str ('WIN', 'LOSS', or 'DRAW')
        - duration: int (battle duration in days)
        - type: str (optional, 'battle' if include_type=True)

    Examples:
        >>> history = [{
        ...     'id': 'battle1', 'user1_id': 'me', 'user2_id': 'rival1',
        ...     'winner_id': 'me', 'end_date': '2026-02-18', 'duration': 5
        ... }]
        >>> rivals = {'rival1': 'Player One'}
        >>> enrich_battle_history(history, 'me', rivals)
        [{'id': 'battle1', 'date': '2026-02-18', 'rival': 'Player One',
          'result': 'WIN', 'duration': 5}]
        >>> enrich_battle_history(history, 'me', rivals, include_type=True)
        [{'id': 'battle1', 'date': '2026-02-18', 'rival': 'Player One',
          'result': 'WIN', 'duration': 5, 'type': 'battle'}]

    Used By:
        - routers.users.get_profile() (replaces lines 132-151)
        - routers.users.get_public_profile() (replaces lines 336-353)

    Result Logic:
        - WIN: Current user's ID matches winner_id
        - LOSS: Rival's ID matches winner_id
        - DRAW: Neither matches (winner_id is None or different)

    Edge Cases:
        - Missing winner_id results in 'DRAW'
        - Missing rival in rivals_map results in 'Unknown' username
        - Missing duration defaults to 5
    """
    enriched = []

    for battle in match_history:
        rival_id = battle['user2_id'] if battle['user1_id'] == user_id else battle['user1_id']
        rival_name = rivals_map.get(rival_id, "Unknown")

        result = "DRAW"
        if battle.get('winner_id') == user_id:
            result = "WIN"
        elif battle.get('winner_id') == rival_id:
            result = "LOSS"

        entry = {
            "id": battle['id'],
            "date": battle['end_date'],
            "rival": rival_name,
            "result": result,
            "duration": battle.get('duration', 5),
        }

        if include_type:
            entry["type"] = "battle"

        enriched.append(entry)

    return enriched
