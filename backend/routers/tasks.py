from fastapi import APIRouter, Depends, HTTPException
from typing import List
from datetime import date, timedelta, datetime
import pytz
from uuid import UUID

from database import supabase
from dependencies import get_current_user
from models import TaskCreate, Task
from utils.quota import get_daily_quota
from utils.game_session import get_active_game_session, get_daily_entry_key
from utils.query_columns import PROFILE_TIMEZONE, TASKS_FULL

router = APIRouter(prefix="/tasks", tags=["tasks"])

def get_user_date(timezone_str: str) -> date:
    """Get user's local date, falling back to UTC for invalid timezones."""
    try:
        tz = pytz.timezone(timezone_str)
        return datetime.now(tz).date()
    except pytz.exceptions.UnknownTimeZoneError:
        return datetime.now(pytz.utc).date()

@router.get("/quota", operation_id="get_daily_quota")
async def get_quota(date_str: str = None, user = Depends(get_current_user)):
    if date_str:
        try:
            target_date = date.fromisoformat(date_str)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format (YYYY-MM-DD)")
    else:
        # Default to tomorrow (planning mode)
        profile_res = supabase.table("profiles").select("timezone").eq("id", user.id).single().execute()
        timezone = profile_res.data['timezone'] if profile_res.data else "UTC"
        user_today = get_user_date(timezone)
        target_date = user_today + timedelta(days=1)
        
    quota = get_daily_quota(target_date)
    return {"date": target_date.isoformat(), "quota": quota}

@router.post("/draft", operation_id="draft_tasks")
async def draft_tasks(tasks: List[TaskCreate], user = Depends(get_current_user)):
    # 1. Get User Profile to know Timezone
    profile_res = supabase.table("profiles").select(PROFILE_TIMEZONE).eq("id", user.id).single().execute()
    if not profile_res.data:
        raise HTTPException(status_code=404, detail="Profile not found")

    profile = profile_res.data

    # 2. Determine "Tomorrow" for the user
    user_today = get_user_date(profile['timezone'])
    user_tomorrow = user_today + timedelta(days=1)

    # Calculate Quota
    quota = get_daily_quota(user_tomorrow)

    # Validate Tasks
    # Filter out empty tasks (empty content) before validation
    non_empty_tasks = [t for t in tasks if t.content and t.content.strip()]
    mandatory_tasks = [t for t in non_empty_tasks if not t.is_optional]
    optional_tasks = [t for t in non_empty_tasks if t.is_optional]

    # Allow incomplete plans - players can save fewer than quota mandatory tasks
    # This motivates them to add more tasks later, and they'll lose points if they don't fill everything
    if len(mandatory_tasks) > quota:
        raise HTTPException(status_code=400, detail=f"You cannot submit more than {quota} mandatory tasks.")

    # Optional tasks are a bonus - only allowed if all mandatory slots are filled
    if len(optional_tasks) > 0 and len(mandatory_tasks) < quota:
        raise HTTPException(status_code=400, detail=f"You must fill all {quota} mandatory task slots before adding optional bonus tasks.")

    if len(mandatory_tasks) == 0 and len(optional_tasks) == 0:
        raise HTTPException(status_code=400, detail="You must submit at least one task.")

    if len(optional_tasks) > 2:
        raise HTTPException(status_code=400, detail="You can only submit up to 2 optional tasks.")

    # 3. Check/Create Daily Entry for Tomorrow
    # REFACTOR-003: Use game session helper to abstract battle mode
    # This supports both PVP battles and future adventure mode
    session_id, game_mode = get_active_game_session(user.id)

    # Get the appropriate daily entry key based on game mode
    entry_key = get_daily_entry_key(session_id, game_mode)

    # Check if entry exists
    # Need to select battle_id and adventure_id for entry matching logic
    entry_res = supabase.table("daily_entries").select("id, battle_id, adventure_id")\
        .eq("user_id", user.id)\
        .eq("date", user_tomorrow.isoformat())\
        .execute()

    # Filter to find entry matching this session
    existing_entry = None
    if entry_res.data:
        for entry in entry_res.data:
            # Check if this entry belongs to our session
            if game_mode.value == "pvp" and entry.get("battle_id") == session_id:
                existing_entry = entry
                break
            elif game_mode.value == "adventure" and entry.get("adventure_id") == session_id:
                existing_entry = entry
                break

    if existing_entry:
        entry_id = existing_entry['id']
        # Clear existing draft tasks
        supabase.table("tasks").delete().eq("daily_entry_id", entry_id).execute()
    else:
        # Create new entry with the appropriate key
        new_entry_data = {
            "user_id": user.id,
            "date": user_tomorrow.isoformat(),
            "is_locked": False
        }
        # Add battle_id or adventure_id based on game mode
        new_entry_data.update(entry_key)

        new_entry = supabase.table("daily_entries").insert(new_entry_data).execute()
        entry_id = new_entry.data[0]['id']
        
    # 4. Insert Tasks
    task_data = []

    for t in mandatory_tasks:
        task_data.append({
            "daily_entry_id": entry_id,
            "content": t.content,
            "is_optional": False,
        })

    for t in optional_tasks:
        task_data.append({
            "daily_entry_id": entry_id,
            "content": t.content,
            "is_optional": True,
        })
    
    if task_data:
        supabase.table("tasks").insert(task_data).execute()
        
    return {"status": "success", "date": user_tomorrow}

@router.get("/today", response_model=List[Task], operation_id="get_today_tasks")
async def get_today_tasks(user = Depends(get_current_user)):
    # 1. Get User Profile
    profile_res = supabase.table("profiles").select(PROFILE_TIMEZONE).eq("id", user.id).single().execute()
    if not profile_res.data:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    profile = profile_res.data
    user_today = get_user_date(profile['timezone'])
    
    # 2. Find Daily Entry for Today
    # We join with tasks manually or via separate query
    # First get entry
    entry_res = supabase.table("daily_entries").select("id")\
        .eq("user_id", user.id)\
        .eq("date", user_today.isoformat())\
        .execute()
        
    if not entry_res.data:
        return []
        
    entry_id = entry_res.data[0]['id']
    
    # 3. Get Tasks
    tasks_res = supabase.table("tasks").select(TASKS_FULL).eq("daily_entry_id", entry_id).execute()
    return tasks_res.data

@router.get("/draft", response_model=List[Task], operation_id="get_draft_tasks")
async def get_draft_tasks(user = Depends(get_current_user)):
    # 1. Get User Profile
    profile_res = supabase.table("profiles").select(PROFILE_TIMEZONE).eq("id", user.id).single().execute()
    if not profile_res.data:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    profile = profile_res.data
    user_today = get_user_date(profile['timezone'])
    user_tomorrow = user_today + timedelta(days=1)
    
    # 2. Find Daily Entry for Tomorrow
    entry_res = supabase.table("daily_entries").select("id")\
        .eq("user_id", user.id)\
        .eq("date", user_tomorrow.isoformat())\
        .execute()
        
    if not entry_res.data:
        return []
        
    entry_id = entry_res.data[0]['id']
    
    # 3. Get Tasks
    tasks_res = supabase.table("tasks").select(TASKS_FULL).eq("daily_entry_id", entry_id).execute()
    return tasks_res.data

@router.post("/{task_id}/complete", operation_id="complete_task")
async def complete_task(task_id: UUID, proof_url: str = None, user = Depends(get_current_user)):
    # 1. Verify Task belongs to user
    # We can do this by joining tables, or just checking if the task exists and links to a daily entry owned by the user.
    # Supabase RLS handles the security, but we need to return a proper error if it fails or returns nothing.
    
    # Update the task
    update_data = {"is_completed": True}
    if proof_url:
        update_data["proof_url"] = proof_url
        
    res = supabase.table("tasks").update(update_data).eq("id", str(task_id)).execute()
    
    if not res.data:
        raise HTTPException(status_code=404, detail="Task not found or not authorized")
        
    return {"status": "success", "task": res.data[0]}
