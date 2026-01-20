"""
Game mode enums and constants.

REFACTOR-004: Add GameMode enum for clear distinction between game types.
This provides type safety and clarity as we add single player adventure mode.
"""
from enum import Enum
from typing import Union


class GameMode(str, Enum):
    """
    Game mode type enum.

    Defines the different game modes available in ProductivityGo.
    Uses str enum for easy serialization and string comparison.

    Attributes:
        PVP: Player vs Player competitive battles
        ADVENTURE: Single player adventure mode (coming soon)
    """
    PVP = "pvp"
    ADVENTURE = "adventure"


# Type alias for game session ID (can be battle_id or adventure_id)
GameSessionID = Union[str, None]
