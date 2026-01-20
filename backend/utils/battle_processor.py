"""
Utility functions for processing battle rounds and state updates.

Shared logic used by both the scheduler and lazy evaluation.
"""
from datetime import date, timedelta, datetime
import pytz
from database import supabase


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
        # Invalid timezone string, fall back to UTC
        return datetime.now(pytz.utc).date()


def process_battle_rounds(battle: dict) -> int:
    """
    Process pending rounds for a battle if both players have finished their day.
    
    This function is shared between:
    - APScheduler (hourly background job)
    - Lazy Evaluation (on dashboard load)
    
    Args:
        battle: Battle dict from database
    
    Returns:
        Number of rounds processed
    """
    battle_id = battle['id']
    start_date = date.fromisoformat(battle['start_date'])
    duration = battle.get('duration', 5)
    current_round = battle.get('current_round', 0)
    
    # Fetch both players' timezones
    user1_id = battle['user1_id']
    user2_id = battle['user2_id']
    
    user1_profile = supabase.table("profiles").select("timezone").eq("id", user1_id).single().execute()
    user2_profile = supabase.table("profiles").select("timezone").eq("id", user2_id).single().execute()
    
    tz1 = user1_profile.data['timezone'] if user1_profile.data else "UTC"
    tz2 = user2_profile.data['timezone'] if user2_profile.data else "UTC"
    
    # Get local dates for both players
    date1 = get_local_date(tz1)
    date2 = get_local_date(tz2)
    
    # Check how many rounds should be processed
    days_since_start = (date.today() - start_date).days
    rounds_to_process = min(days_since_start, duration)
    
    if current_round >= rounds_to_process:
        # Already up to date
        return 0
    
    # Process pending rounds
    rounds_processed = 0
    for r in range(current_round, rounds_to_process):
        round_date = start_date + timedelta(days=r)
        
        # CRITICAL: Only process if BOTH players have finished this day
        if date1 > round_date and date2 > round_date:
            print(f"[BATTLE_PROCESSOR] Processing round {r} for battle {battle_id} (Date: {round_date})")
            try:
                # Call the database function to calculate round
                rpc_result = supabase.rpc("calculate_daily_round", {
                    "battle_uuid": battle_id,
                    "round_date": round_date.isoformat()
                }).execute()

                # BUG-004 FIX: Validate RPC response before proceeding
                if rpc_result.data is None:
                    print(f"[BATTLE_PROCESSOR] RPC returned None for round {r} of battle {battle_id}")
                    break

                # Extract data - handle both list and dict responses
                data = rpc_result.data[0] if isinstance(rpc_result.data, list) else rpc_result.data

                # Validate we got expected data structure
                if data is None:
                    print(f"[BATTLE_PROCESSOR] RPC data is None for round {r} of battle {battle_id}")
                    break

                # Update round count only after validating RPC succeeded
                current_round += 1
                supabase.table("battles").update({"current_round": current_round}).eq("id", battle_id).execute()
                rounds_processed += 1

                # Log successful round processing with XP values
                user1_xp = data.get('user1_xp', 0)
                user2_xp = data.get('user2_xp', 0)
                print(f"[BATTLE_PROCESSOR] Round {r} processed successfully: user1_xp={user1_xp}, user2_xp={user2_xp}")

            except Exception as e:
                print(f"[BATTLE_PROCESSOR] Error processing round {r} for battle {battle_id}: {e}")
                break
        else:
            # Can't process this round yet, stop
            break
    
    # Check if battle is complete
    if current_round >= duration and battle['status'] == 'active':
        print(f"[BATTLE_PROCESSOR] Battle {battle_id} is complete, finalizing...")
        try:
            result = supabase.rpc("complete_battle", {"battle_uuid": battle_id}).execute()

            # BUG-004 FIX: Validate RPC response
            if result.data is None:
                print(f"[BATTLE_PROCESSOR] complete_battle RPC returned None for battle {battle_id}")
            else:
                # Extract data - handle both list and dict responses
                data = result.data[0] if isinstance(result.data, list) else result.data
                if data is None:
                    print(f"[BATTLE_PROCESSOR] complete_battle data is None for battle {battle_id}")
                else:
                    winner_id = data.get('winner_id') if data else None
                    print(f"[BATTLE_PROCESSOR] Battle {battle_id} completed successfully, winner: {winner_id}")
        except Exception as e:
            print(f"[BATTLE_PROCESSOR] Error completing battle {battle_id}: {e}")
    
    return rounds_processed
