"""
Timezone and Date Utilities

Centralized utilities for handling timezone-aware date calculations.
Used by battle processing, adventure processing, and task planning.

REFACTOR-007: Extracted from 4 duplicate implementations across:
- backend/utils/battle_processor.py
- backend/utils/adventure_processor.py
- backend/routers/battles.py
- backend/routers/tasks.py
"""
from datetime import date, datetime
import pytz
from utils.logging_config import get_logger

logger = get_logger(__name__)


def get_local_date(tz_str: str) -> date:
    """
    Get the current local date for a given timezone.

    Falls back to UTC for invalid timezones and logs at debug level.
    This is critical for fair-play - users in different timezones
    need consistent round processing based on their local midnight.

    Args:
        tz_str: IANA timezone string (e.g., 'America/New_York', 'Asia/Tokyo')

    Returns:
        Current date in the specified timezone, or UTC if invalid

    Examples:
        >>> get_local_date('America/New_York')
        datetime.date(2026, 2, 18)
        >>> get_local_date('Invalid/Timezone')  # Falls back to UTC
        datetime.date(2026, 2, 18)

    Edge Cases:
        - Invalid timezone strings fall back to UTC with debug log
        - Empty string falls back to UTC with debug log
        - None raises TypeError (caller should provide default)

    Used By:
        - utils.battle_processor.process_battle_rounds()
        - utils.adventure_processor.process_adventure_rounds()
        - routers.battles.get_current_battle()
        - routers.tasks.draft_tasks(), get_tasks(), complete_task()
    """
    try:
        return datetime.now(pytz.timezone(tz_str)).date()
    except pytz.exceptions.UnknownTimeZoneError:
        logger.debug(f"Unknown timezone: '{tz_str}', falling back to UTC")
        return datetime.now(pytz.utc).date()
