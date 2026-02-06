"""
Shared utility for stats calculations.

REFACTOR-002: Extracted from routers/battles.py and routers/users.py
to provide single source of truth for win rate calculation.
"""
from typing import Union


def calculate_win_rate(wins: int, total: int) -> float:
    """
    Calculate win rate as a percentage.

    This function safely handles division by zero and returns
    a formatted percentage rounded to 1 decimal place.

    Args:
        wins: Number of wins
        total: Total number of battles

    Returns:
        Win rate as a float percentage (0.0 to 100.0), rounded to 1 decimal

    Examples:
        >>> calculate_win_rate(5, 10)
        50.0
        >>> calculate_win_rate(7, 12)
        58.3
        >>> calculate_win_rate(0, 0)
        0.0
    """
    if total <= 0:
        return 0.0
    return round((wins / total) * 100, 1)


def format_win_rate(wins: int, total: int) -> str:
    """
    Format win rate as a string with percentage sign.

    Convenience function for displaying win rate in UI responses.

    Args:
        wins: Number of wins
        total: Total number of battles

    Returns:
        Win rate as a formatted string (e.g., "50.0%", "58.3%")

    Examples:
        >>> format_win_rate(5, 10)
        '50.0%'
        >>> format_win_rate(7, 12)
        '58.3%'
    """
    return f"{calculate_win_rate(wins, total)}%"
