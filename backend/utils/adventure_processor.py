"""
Adventure Round Processor

Utility for processing adventure rounds:
- Called by scheduler hourly
- Called by lazy evaluation on dashboard load
- Handles deadline checking and completion

REFACTOR-007: Uses centralized logging system.
"""
from datetime import date, timedelta, datetime
import pytz
from typing import Optional, Dict, Any
from database import supabase
from utils.logging_config import get_logger

logger = get_logger(__name__)


def get_local_date(tz_str: str) -> date:
    """
    Get the current local date for a given timezone.

    Falls back to UTC if timezone is invalid.

    Args:
        tz_str: Timezone string (e.g., 'America/New_York')

    Returns:
        Current date in the specified timezone, or UTC if invalid
    """
    try:
        return datetime.now(pytz.timezone(tz_str)).date()
    except pytz.exceptions.UnknownTimeZoneError:
        logger.warning(f"Unknown timezone: {tz_str}, falling back to UTC")
        return datetime.now(pytz.utc).date()


def process_adventure_rounds(adventure: Dict[str, Any]) -> int:
    """
    Process pending rounds for an adventure.

    This function is shared between:
    - APScheduler (hourly background job)
    - Lazy Evaluation (on dashboard load)

    Args:
        adventure: Adventure dict with monster data

    Returns:
        Number of rounds processed
    """
    adventure_id = adventure['id']

    # Skip if not active
    if adventure.get('status') != 'active':
        logger.debug(f"Adventure {adventure_id} is not active, skipping")
        return 0

    # Get user timezone
    user_id = adventure['user_id']
    profile_res = supabase.table("profiles").select("timezone")\
        .eq("id", user_id).single().execute()

    user_tz = "UTC"
    if profile_res.data and profile_res.data.get('timezone'):
        user_tz = profile_res.data['timezone']

    # Get current date in user's timezone
    user_today = get_local_date(user_tz)

    # Parse adventure dates
    start_date = date.fromisoformat(adventure['start_date'])
    deadline = date.fromisoformat(adventure['deadline'])
    current_round = adventure.get('current_round', 0)

    # Handle break day status
    if adventure.get('is_on_break'):
        break_end_str = adventure.get('break_end_date')
        if break_end_str:
            break_end_date = date.fromisoformat(break_end_str)
            if user_today > break_end_date:
                # Clear break status - break has ended
                logger.info(f"Clearing break status for adventure {adventure_id}")
                supabase.table("adventures").update({
                    "is_on_break": False,
                    "break_end_date": None
                }).eq("id", adventure_id).execute()
            else:
                # Still on break, no processing
                logger.debug(f"Adventure {adventure_id} is on break until {break_end_date}")
                return 0
        else:
            # Break flag set but no end date - clear it
            logger.warning(f"Adventure {adventure_id} has is_on_break=True but no break_end_date, clearing")
            supabase.table("adventures").update({
                "is_on_break": False,
                "break_end_date": None
            }).eq("id", adventure_id).execute()

    rounds_processed = 0

    # Process each completed day
    days_since_start = (user_today - start_date).days

    for day_offset in range(current_round, days_since_start):
        round_date = start_date + timedelta(days=day_offset)

        # Only process days that have fully passed
        if round_date >= user_today:
            break

        logger.debug(f"Processing round {day_offset + 1} for adventure {adventure_id} (Date: {round_date})")

        try:
            result = supabase.rpc("calculate_adventure_round", {
                "adventure_uuid": adventure_id,
                "round_date": round_date.isoformat()
            }).execute()

            # Validate RPC response
            if result.data is None:
                logger.warning(f"RPC returned None for round {day_offset + 1} of adventure {adventure_id}")
                break

            # Extract data - handle both list and dict responses
            data = result.data[0] if isinstance(result.data, list) else result.data

            if data is None:
                logger.warning(f"RPC data is None for round {day_offset + 1} of adventure {adventure_id}")
                break

            rounds_processed += 1
            logger.info(f"Processed round {day_offset + 1} for adventure {adventure_id}")

        except Exception as e:
            logger.error(f"Error processing round {day_offset + 1} for adventure {adventure_id}: {e}")
            break

    # Check for victory/defeat conditions after processing rounds
    if rounds_processed > 0:
        # Reload adventure to get updated HP
        updated = supabase.table("adventures").select("monster_current_hp, status")\
            .eq("id", adventure_id).single().execute()

        if updated.data:
            # Check victory (HP <= 0)
            if updated.data['monster_current_hp'] <= 0:
                logger.info(f"Adventure {adventure_id} - Monster defeated!")
                complete_adventure(adventure_id)

    # Check deadline (escape) - monster escapes if deadline passed
    if user_today > deadline:
        # Reload to ensure we have current status
        status_check = supabase.table("adventures").select("status")\
            .eq("id", adventure_id).single().execute()

        if status_check.data and status_check.data['status'] == 'active':
            logger.info(f"Adventure {adventure_id} - Deadline passed, monster escaped")
            complete_adventure(adventure_id)

    return rounds_processed


def complete_adventure(adventure_id: str) -> Optional[Dict[str, Any]]:
    """
    Complete an adventure using the SQL function.

    This handles:
    - XP calculation
    - Rating updates (defeats/escapes)
    - Status change to completed
    - Profile current_adventure clearing

    Args:
        adventure_id: Adventure UUID

    Returns:
        Completion data dict with victory status and XP earned, or None if failed
    """
    try:
        result = supabase.rpc("complete_adventure", {
            "adventure_uuid": adventure_id
        }).execute()

        if result.data is None:
            logger.warning(f"complete_adventure RPC returned None for adventure {adventure_id}")
            return None

        # Extract data - handle both list and dict responses
        data = result.data[0] if isinstance(result.data, list) else result.data

        if data is None:
            logger.warning(f"complete_adventure data is None for adventure {adventure_id}")
            return None

        is_victory = data.get('is_victory', False)
        xp_earned = data.get('xp_earned', 0)

        logger.info(
            f"Adventure {adventure_id} completed: "
            f"victory={is_victory}, xp={xp_earned}"
        )

        return data

    except Exception as e:
        logger.error(f"Error completing adventure {adventure_id}: {e}")
        return None
