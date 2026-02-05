"""
Game session detection and management utilities.

REFACTOR-003: Abstract battle mode from task endpoints.
This helper provides a unified interface for finding the user's active game session,
whether it's a PVP battle or (in the future) an adventure mode session.
"""
from typing import Tuple, Union, Optional

from database import supabase
from fastapi import HTTPException
from utils.enums import GameMode


def get_active_game_session(user_id: str) -> Tuple[str, GameMode]:
    """
    Get the active game session for a user.

    This function checks for active game sessions in priority order:
    1. Active PVP battle
    2. Active adventure (future - placeholder for now)

    Args:
        user_id: The UUID of the user

    Returns:
        Tuple of (session_id, game_mode) where:
        - session_id: The UUID of the battle or adventure
        - game_mode: GameMode.PVP or GameMode.ADVENTURE

    Raises:
        HTTPException: If no active game session is found (400)

    Examples:
        >>> session_id, mode = get_active_game_session("user-123")
        >>> print(f"Active session: {mode.value} - {session_id}")
        Active session: pvp - battle-456

    Note:
        Battle mode takes priority over adventure mode if both exist
        (though a user should only have one active session at a time).
    """
    # 1. Check for active PVP battle
    battle_res = supabase.table("battles").select("id")\
        .or_(f"user1_id.eq.{user_id},user2_id.eq.{user_id}")\
        .eq("status", "active")\
        .single().execute()

    if battle_res.data:
        return battle_res.data['id'], GameMode.PVP

    # 2. Check for active adventure
    adventure_res = supabase.table("adventures").select("id")\
        .eq("user_id", user_id)\
        .eq("status", "active")\
        .single().execute()

    if adventure_res.data:
        return adventure_res.data['id'], GameMode.ADVENTURE

    # 3. No active session found
    raise HTTPException(
        status_code=400,
        detail="No active battle or adventure found. Join a battle or start an adventure to plan tasks."
    )


def get_daily_entry_key(session_id: str, game_mode: GameMode) -> dict:
    """
    Get the appropriate daily entry lookup key based on game mode.

    For PVP battles, daily entries are linked via battle_id.
    For adventures, they will be linked via adventure_id (future).

    Args:
        session_id: The UUID of the battle or adventure
        game_mode: The game mode (PVP or ADVENTURE)

    Returns:
        Dictionary with the appropriate key for daily_entries table lookup

    Examples:
        >>> key = get_daily_entry_key("battle-123", GameMode.PVP)
        >>> key
        {'battle_id': 'battle-123'}

        >>> key = get_daily_entry_key("adventure-456", GameMode.ADVENTURE)
        >>> key
        {'adventure_id': 'adventure-456'}
    """
    if game_mode == GameMode.PVP:
        return {"battle_id": session_id}
    elif game_mode == GameMode.ADVENTURE:
        return {"adventure_id": session_id}
    else:
        # This should never happen with proper enum usage
        raise ValueError(f"Unknown game mode: {game_mode}")


def has_active_game_session(user_id: str) -> bool:
    """
    Check if user has any active game session without raising an exception.

    This is useful for conditional logic where you want to check
    for a session without triggering an HTTP error.

    Args:
        user_id: The UUID of the user

    Returns:
        True if user has an active battle or adventure, False otherwise

    Examples:
        >>> if has_active_game_session("user-123"):
        ...     session_id, mode = get_active_game_session("user-123")
    """
    try:
        get_active_game_session(user_id)
        return True
    except HTTPException:
        return False
