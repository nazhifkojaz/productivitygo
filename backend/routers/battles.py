from fastapi import APIRouter, Depends, HTTPException
from typing import List
from datetime import date, timedelta, datetime
import pytz

from database import supabase
from dependencies import get_current_user
from services.battle_service import BattleService
from services.battle_query_service import BattleQueryService
from utils.rank_calculations import calculate_rank
from utils.battle_helpers import (
    extract_user_profiles,
    calculate_app_state,
    build_rival_intelligence
)
from utils.query_columns import BATTLE_RELOAD
from utils.timezone import get_local_date
from utils.logging_config import get_logger

router = APIRouter(prefix="/battles", tags=["battles"])
logger = get_logger(__name__)

@router.get("/current", operation_id="get_current_battle")
async def get_current_battle(user = Depends(get_current_user)):
    """
    Get the current active battle with full context.

    This endpoint orchestrates multiple services to build a complete
    battle response including:
    - Battle data with embedded profiles
    - Lazy round processing
    - App state calculation
    - Rival intelligence
    - User progress tracking

    REFACTOR-005: Refactored to use extracted helper functions and services.
    """
    # Step 1: Fetch battle with embedded profiles
    battle = await BattleQueryService.fetch_active_battle_with_profiles(user.id)

    if not battle:
        raise HTTPException(status_code=404, detail="No active battle found")

    start_date = date.fromisoformat(battle['start_date'])
    end_date = date.fromisoformat(battle['end_date'])

    # Step 2: Lazy evaluation trigger (backup)
    if battle['status'] == 'active':
        from utils.battle_processor import process_battle_rounds
        rounds_processed = await process_battle_rounds(battle)
        if rounds_processed > 0:
            updated_fields = await BattleQueryService.reload_battle_state(battle['id'])
            if updated_fields:
                battle.update(updated_fields)

    # Step 3: Extract profiles with null handling
    user_profile, rival_profile, rival_id = extract_user_profiles(battle, user.id)

    # Step 4: Calculate app state
    user_tz = user_profile.get('timezone', 'UTC')
    user_today = get_local_date(user_tz)

    app_state = calculate_app_state(
        battle['status'],
        start_date,
        end_date,
        user_today
    )
    battle['app_state'] = app_state

    # Step 5: Lazy evaluation trigger (fair mode) - round processing
    duration = battle.get('duration', 5)
    current_round = battle.get('current_round', 0)

    if battle['status'] == 'active':
        # Get both players' local dates
        user1_data = battle['user1'] or {'timezone': 'UTC'}
        user2_data = battle['user2'] or {'timezone': 'UTC'}
        date1 = get_local_date(user1_data.get('timezone', 'UTC'))
        date2 = get_local_date(user2_data.get('timezone', 'UTC'))

        days_since_start = (user_today - start_date).days
        rounds_to_process = min(days_since_start, duration)

        if current_round < rounds_to_process:
            for r in range(current_round, rounds_to_process):
                round_date = start_date + timedelta(days=r)
                if date1 > round_date and date2 > round_date:
                    logger.debug(f"Processing round {r} (Date {round_date}) - Passed for both")
                    try:
                        rpc_result = await supabase.rpc("calculate_daily_round", {
                            "battle_uuid": battle['id'],
                            "round_date": round_date.isoformat()
                        }).execute()

                        if rpc_result.data is None:
                            logger.warning(f"Lazy Eval: RPC returned None for round {r}, stopping processing")
                            break

                        current_round += 1
                        await supabase.table("battles").update({"current_round": current_round}).eq("id", battle['id']).execute()

                    except Exception as e:
                        logger.error(f"Error in lazy evaluation for round {r} of battle {battle['id']}: {e}")
                        break
                else:
                    break

            battle['current_round'] = current_round

        if current_round >= duration:
            logger.info(f"Battle {battle['id']} is complete, marking as completed")
            try:
                result = await BattleService.complete_battle(battle['id'])
                if result:
                    battle['status'] = 'completed'
                    if result.get('already_completed'):
                        logger.debug(f"Battle {battle['id']} was already completed by another process (safe idempotent call)")
            except Exception as e:
                logger.error(f"Error auto-completing battle {battle['id']}: {e}")

    # Step 6: Build rival intelligence
    if app_state in ['IN_BATTLE', 'LAST_BATTLE_DAY']:
        today_str = date.today().isoformat()
        total_tasks, completed_tasks = await BattleQueryService.fetch_rival_tasks_for_today(
            rival_id, today_str
        )
    else:
        total_tasks, completed_tasks = 0, 0

    battle['rival'] = build_rival_intelligence(
        rival_profile,
        total_tasks,
        completed_tasks
    )

    # Step 7: Calculate rounds played
    battle['rounds_played'] = await BattleQueryService.calculate_rounds_played(
        battle['id'], user.id
    )

    return battle

@router.post("/{battle_id}/forfeit", operation_id="forfeit_battle")
async def forfeit_battle(battle_id: str, user = Depends(get_current_user)):
    """
    Forfeit an active battle.
    """
    return await BattleService.forfeit_battle(battle_id, user.id)

@router.post("/{battle_id}/leave", operation_id="leave_battle")
async def leave_battle(battle_id: str, user = Depends(get_current_user)):
    """
    Leave a battle result screen.
    """
    try:
        await supabase.table("profiles").update({"current_battle": None}).eq("id", user.id).execute()
        return {"status": "left"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to leave battle: {str(e)}")

@router.post("/{battle_id}/complete", operation_id="complete_battle")
async def complete_battle(battle_id: str, user = Depends(get_current_user)):
    return await BattleService.complete_battle(battle_id)

@router.post("/{battle_id}/daily-round", operation_id="calculate_daily_round")
async def calculate_round(battle_id: str, round_date: str = None, user = Depends(get_current_user)):
    """
    [DEBUG ONLY] Manually calculate daily round for a specific date.
    """
    from config import DEBUG_MODE
    if not DEBUG_MODE:
        raise HTTPException(status_code=404, detail="Endpoint not available in production mode")

    return await BattleService.calculate_round(battle_id, round_date)


@router.get("/{battle_id}", operation_id="get_battle_details")
async def get_battle_details(battle_id: str, user = Depends(get_current_user)):
    # Fetch battle details including profiles
    # We need stats to calculate rank
    res = await supabase.table("battles").select(
        "*, user1:profiles!user1_id(username, level, battle_count, battle_win_count), user2:profiles!user2_id(username, level, battle_count, battle_win_count)"
    ).eq("id", battle_id).execute()

    if not res.data:
        raise HTTPException(status_code=404, detail="Battle not found")

    battle = res.data[0]

    # Calculate Ranks
    if battle.get('user1'):
        u1 = battle['user1']
        u1['rank'] = calculate_rank(u1.get('level', 1), u1.get('battle_count', 0), u1.get('battle_win_count', 0))

    if battle.get('user2'):
        u2 = battle['user2']
        u2['rank'] = calculate_rank(u2.get('level', 1), u2.get('battle_count', 0), u2.get('battle_win_count', 0))

    # Fetch Daily Breakdown
    entries_res = await supabase.table("daily_entries").select("date, user_id, daily_xp")\
        .eq("battle_id", battle_id)\
        .order("date")\
        .execute()

    breakdown = {}
    user1_total = 0
    user2_total = 0

    if entries_res.data:
        for entry in entries_res.data:
            d = entry['date']
            uid = entry['user_id']
            xp = entry.get('daily_xp', 0) or 0

            if d not in breakdown:
                breakdown[d] = {'date': d, 'user1_xp': 0, 'user2_xp': 0}

            if uid == battle['user1_id']:
                breakdown[d]['user1_xp'] = xp
                user1_total += xp
            elif uid == battle['user2_id']:
                breakdown[d]['user2_xp'] = xp
                user2_total += xp

    # Determine daily winners
    daily_stats = []
    for d in sorted(breakdown.keys()):
        day_data = breakdown[d]
        u1 = day_data['user1_xp']
        u2 = day_data['user2_xp']
        winner = None
        if u1 > u2: winner = battle['user1_id']
        elif u2 > u1: winner = battle['user2_id']

        daily_stats.append({
            'date': d,
            'user1_xp': u1,
            'user2_xp': u2,
            'winner_id': winner
        })

    battle['daily_breakdown'] = daily_stats
    battle['scores'] = {
        'user1_xp': user1_total,
        'user2_xp': user2_total
    }

    return battle

