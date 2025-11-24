from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from database import supabase
from typing import Optional

router = APIRouter(prefix="/users", tags=["users"])

class UserUpdate(BaseModel):
    username: Optional[str] = None
    avatar_url: Optional[str] = None

from dependencies import get_current_user

@router.put("/profile", operation_id="update_profile")
def update_profile(update_data: UserUpdate, user = Depends(get_current_user)):
    try:
        # Update profile in 'profiles' table
        data = {}
        if update_data.username:
            data["username"] = update_data.username
            
        if not data:
            return {"message": "No changes provided"}

        # Use upsert to ensure profile exists
        data["id"] = user.id
        response = supabase.table("profiles").upsert(data).execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/profile", operation_id="get_profile")
def get_profile(user = Depends(get_current_user)):
    try:
        # Fetch Profile
        response = supabase.table("profiles").select("*").eq("id", user.id).single().execute()
        profile = response.data
        
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")

        # Calculate Stats from Battles
        # Wins: Count battles where status='completed' and winner_id=user.id (Assuming we have winner_id logic later, for now just count completed as placeholder or 0)
        # Actually, we don't have winner_id yet. Let's just count 'completed' battles for now as "Battles Played" or similar.
        # Wait, user asked for "Battles Won". Since we don't have scoring yet, I'll return 0 for now but structure it so it's easy to add.
        
        # Streak: Count consecutive days of task completion (This requires task history, complex).
        # For MVP, let's just return 0 placeholders but explicitly in the API so frontend doesn't guess.
        
        profile["stats"] = {
            "battle_wins": profile.get("overall_win_count", 0),
            "total_xp": profile.get("total_xp_earned", 0),
            "rounds_won": profile.get("daily_win_count", 0),
            "win_rate": f"{profile.get('overall_win_rate', 0)}%",
            "tasks_completed": profile.get("completed_tasks", 0)
        }
        
        return profile
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
