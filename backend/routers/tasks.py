from fastapi import APIRouter, Depends, HTTPException
from typing import List
from datetime import date, timedelta, datetime
import pytz
from uuid import UUID

from database import supabase
from dependencies import get_current_user
from models import TaskCreate, Task
from utils.quota import get_daily_quota

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
    profile_res = supabase.table("profiles").select("*").eq("id", user.id).single().execute()
    if not profile_res.data:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    profile = profile_res.data
    
    # 2. Determine "Tomorrow" for the user
    user_today = get_user_date(profile['timezone'])
    user_tomorrow = user_today + timedelta(days=1)
    
    # Calculate Quota
    quota = get_daily_quota(user_tomorrow)
    
    # Validate Tasks
    mandatory_tasks = [t for t in tasks if not t.is_optional]
    optional_tasks = [t for t in tasks if t.is_optional]
    
    if len(mandatory_tasks) > quota:
        raise HTTPException(status_code=400, detail=f"You cannot submit more than {quota} mandatory tasks.")
    
    if len(mandatory_tasks) == 0 and len(optional_tasks) == 0:
         raise HTTPException(status_code=400, detail="You must submit at least one task.")
        
    if len(optional_tasks) > 2:
        raise HTTPException(status_code=400, detail="You can only submit up to 2 optional tasks.")
    
    # 3. Check/Create Daily Entry for Tomorrow
    # We need a battle_id. For MVP, let's assume the user is in an active battle.
    # Find active battle for user
    battle_res = supabase.table("battles").select("id")\
        .or_(f"user1_id.eq.{user.id},user2_id.eq.{user.id}")\
        .eq("status", "active")\
        .single().execute()
        
    if not battle_res.data:
        # For testing/MVP, if no battle exists, maybe we can't plan? 
        # Or we create a dummy entry? Let's enforce Battle for now.
        raise HTTPException(status_code=400, detail="No active battle found. You must be in a battle to plan tasks.")
    
    battle_id = battle_res.data['id']
    
    # Check if entry exists
    entry_res = supabase.table("daily_entries").select("id")\
        .eq("battle_id", battle_id)\
        .eq("user_id", user.id)\
        .eq("date", user_tomorrow.isoformat())\
        .execute()
        
    if entry_res.data:
        entry_id = entry_res.data[0]['id']
        # Clear existing draft tasks
        supabase.table("tasks").delete().eq("daily_entry_id", entry_id).execute()
    else:
        # Create new entry
        new_entry = supabase.table("daily_entries").insert({
            "battle_id": battle_id,
            "user_id": user.id,
            "date": user_tomorrow.isoformat(),
            "is_locked": False
        }).execute()
        entry_id = new_entry.data[0]['id']
        
    # Calculate Scores
    # Mandatory: 100 points distributed evenly
    # Optional: 5 points each
    mandatory_score_base = 100 // quota
    mandatory_remainder = 100 % quota
    
    # 4. Insert Tasks
    task_data = []
    
    # Process Mandatory Tasks
    for i, t in enumerate(mandatory_tasks):
        # Distribute remainder to first few tasks
        score = mandatory_score_base + (1 if i < mandatory_remainder else 0)
        task_data.append({
            "daily_entry_id": entry_id,
            "content": t.content,
            "is_optional": False,
            "assigned_score": score
        })
        
    # Process Optional Tasks
    for t in optional_tasks:
        task_data.append({
            "daily_entry_id": entry_id,
            "content": t.content,
            "is_optional": True,
            "assigned_score": 5
        })
    
    if task_data:
        supabase.table("tasks").insert(task_data).execute()
        
    return {"status": "success", "date": user_tomorrow}

@router.get("/today", response_model=List[Task], operation_id="get_today_tasks")
async def get_today_tasks(user = Depends(get_current_user)):
    # 1. Get User Profile
    profile_res = supabase.table("profiles").select("*").eq("id", user.id).single().execute()
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
    tasks_res = supabase.table("tasks").select("*").eq("daily_entry_id", entry_id).execute()
    return tasks_res.data

@router.get("/draft", response_model=List[Task], operation_id="get_draft_tasks")
async def get_draft_tasks(user = Depends(get_current_user)):
    # 1. Get User Profile
    profile_res = supabase.table("profiles").select("*").eq("id", user.id).single().execute()
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
    tasks_res = supabase.table("tasks").select("*").eq("daily_entry_id", entry_id).execute()
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
