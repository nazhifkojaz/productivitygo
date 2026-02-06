"""
Shared utility for daily quota calculation.

REFACTOR-001: Extracted from routers/battles.py and routers/tasks.py
to provide single source of truth for quota calculation.
"""
import hashlib
from datetime import date


def get_daily_quota(date_obj: date) -> int:
    """
    Deterministically returns 3, 4, or 5 based on the date.

    This function uses MD5 hash of the date string to generate a
    consistent daily quota. The same date will always return the
    same quota, allowing for predictable daily task planning.

    Args:
        date_obj: The date to calculate quota for

    Returns:
        An integer value of 3, 4, or 5 representing the daily task quota

    Examples:
        >>> get_daily_quota(date(2026, 1, 15))
        4
        >>> get_daily_quota(date(2026, 1, 16))
        3
    """
    date_str = date_obj.isoformat()
    hash_obj = hashlib.md5(date_str.encode())
    hash_int = int(hash_obj.hexdigest(), 16)
    return (hash_int % 3) + 3
