"""
Adventure Mode API Router

Endpoints:
- GET  /adventures/monsters         - Get weighted monster pool
- POST /adventures/monsters/refresh - Refresh monster pool
- POST /adventures/start            - Start new adventure
- GET  /adventures/current          - Get active adventure
- GET  /adventures/{id}             - Get adventure details
- POST /adventures/{id}/abandon     - Abandon adventure
- POST /adventures/{id}/break       - Schedule break
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from datetime import date, timedelta, datetime
import pytz

from database import supabase
from dependencies import get_current_user
from services.adventure_service import AdventureService
from utils.query_columns import ADVENTURE_WITH_MONSTER, MONSTER_FULL
from utils.logging_config import get_logger

router = APIRouter(prefix="/adventures", tags=["adventures"])
logger = get_logger(__name__)


@router.get("/monsters", operation_id="get_monster_pool")
async def get_monster_pool(user = Depends(get_current_user)):
    """
    Get weighted monster pool for adventure selection.

    Returns 4 monsters weighted by user's rating.
    Higher rating = more high-tier monsters.
    Refresh count resets to 3 for each new adventure session.
    """
    # Get user's rating and initialize refresh count
    profile_res = supabase.table("profiles").select("monster_rating")\
        .eq("id", user.id).single().execute()

    if not profile_res.data:
        raise HTTPException(status_code=404, detail="Profile not found")

    rating = profile_res.data.get('monster_rating', 0)

    # Initialize/refresh count from database (resets if new session)
    remaining = AdventureService.initialize_refresh_count(user.id)

    # Get weighted pool
    pool = AdventureService.get_weighted_monster_pool(rating, count=4)

    return {
        "monsters": pool,
        "refreshes_remaining": remaining,
        "unlocked_tiers": AdventureService.get_unlocked_tiers(rating),
        "current_rating": rating
    }


@router.post("/monsters/refresh", operation_id="refresh_monster_pool")
async def refresh_monster_pool(user = Depends(get_current_user)):
    """
    Refresh monster pool. Max 3 refreshes per adventure start.
    """
    # Get user's rating
    profile_res = supabase.table("profiles").select("monster_rating")\
        .eq("id", user.id).single().execute()

    if not profile_res.data:
        raise HTTPException(status_code=404, detail="Profile not found")

    rating = profile_res.data.get('monster_rating', 0)

    # Decrement refresh count (raises exception if none remaining)
    try:
        remaining = AdventureService.decrement_refresh_count(user.id)
    except HTTPException:
        raise HTTPException(
            status_code=400,
            detail="No refreshes remaining. Select a monster or start over."
        )

    # Get new pool
    pool = AdventureService.get_weighted_monster_pool(rating, count=4)

    return {
        "monsters": pool,
        "refreshes_remaining": remaining,
        "unlocked_tiers": AdventureService.get_unlocked_tiers(rating)
    }


@router.post("/start", operation_id="start_adventure")
async def start_adventure(body: dict, user = Depends(get_current_user)):
    """
    Start a new adventure with the selected monster.

    Body: { "monster_id": "uuid" }
    """
    monster_id = body.get('monster_id')

    if not monster_id:
        raise HTTPException(status_code=400, detail="monster_id is required")

    adventure = AdventureService.create_adventure(user.id, monster_id)

    # Fetch with monster data for response
    full_adventure = supabase.table("adventures").select(ADVENTURE_WITH_MONSTER)\
        .eq("id", adventure['id']).single().execute()

    return full_adventure.data


@router.get("/current", operation_id="get_current_adventure")
async def get_current_adventure(user = Depends(get_current_user)):
    """
    Get the user's active adventure with monster info and app state.
    """
    # Fetch active adventure with monster
    try:
        res = supabase.table("adventures").select(ADVENTURE_WITH_MONSTER)\
            .eq("user_id", user.id)\
            .eq("status", "active")\
            .single().execute()
    except Exception:
        # No active adventure found
        raise HTTPException(status_code=404, detail="No active adventure found")

    if not res.data:
        raise HTTPException(status_code=404, detail="No active adventure found")

    adventure = res.data

    # Get user timezone for app state calculation
    profile_res = supabase.table("profiles").select("timezone")\
        .eq("id", user.id).single().execute()

    user_tz = profile_res.data.get('timezone', 'UTC') if profile_res.data else 'UTC'

    try:
        user_today = datetime.now(pytz.timezone(user_tz)).date()
    except pytz.exceptions.UnknownTimeZoneError:
        user_today = datetime.now(pytz.utc).date()

    # Calculate app state
    start_date = date.fromisoformat(adventure['start_date'])
    deadline = date.fromisoformat(adventure['deadline'])

    if adventure['is_on_break']:
        app_state = 'ON_BREAK'
    elif user_today < start_date:
        app_state = 'PRE_ADVENTURE'
    elif user_today > deadline:
        app_state = 'DEADLINE_PASSED'
    elif user_today == deadline:
        app_state = 'LAST_DAY'
    else:
        app_state = 'ACTIVE'

    adventure['app_state'] = app_state

    # Calculate days remaining
    days_remaining = (deadline - user_today).days
    adventure['days_remaining'] = max(days_remaining, 0)

    return adventure


@router.get("/{adventure_id}", operation_id="get_adventure_details")
async def get_adventure_details(adventure_id: str, user = Depends(get_current_user)):
    """
    Get adventure details including daily breakdown.
    """
    # Fetch adventure with monster
    try:
        res = supabase.table("adventures").select(ADVENTURE_WITH_MONSTER)\
            .eq("id", adventure_id).single().execute()
    except Exception:
        raise HTTPException(status_code=404, detail="Adventure not found")

    if not res.data:
        raise HTTPException(status_code=404, detail="Adventure not found")

    adventure = res.data

    # Verify ownership
    if adventure['user_id'] != user.id:
        raise HTTPException(status_code=403, detail="Not your adventure")

    # Fetch daily breakdown
    entries_res = supabase.table("daily_entries").select("date, daily_xp")\
        .eq("adventure_id", adventure_id)\
        .order("date")\
        .execute()

    daily_breakdown = []
    if entries_res.data:
        for entry in entries_res.data:
            daily_breakdown.append({
                'date': entry['date'],
                'damage': entry.get('daily_xp', 0) or 0
            })

    adventure['daily_breakdown'] = daily_breakdown

    return adventure


@router.post("/{adventure_id}/abandon", operation_id="abandon_adventure")
async def abandon_adventure(adventure_id: str, user = Depends(get_current_user)):
    """
    Abandon adventure early. Receives 50% of earned XP.
    """
    return AdventureService.abandon_adventure(adventure_id, user.id)


@router.post("/{adventure_id}/break", operation_id="schedule_break")
async def schedule_break(adventure_id: str, user = Depends(get_current_user)):
    """
    Schedule tomorrow as a break day.

    Extends deadline by 1 day. Max 2 breaks per adventure.
    """
    return AdventureService.schedule_break(adventure_id, user.id)
