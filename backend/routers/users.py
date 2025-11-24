from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from database import supabase
from typing import Optional

router = APIRouter(prefix="/users", tags=["users"])

class UserUpdate(BaseModel):
    username: Optional[str] = None
    avatar_url: Optional[str] = None
    avatar_emoji: Optional[str] = None

from dependencies import get_current_user

@router.put("/profile", operation_id="update_profile")
def update_profile(update_data: UserUpdate, user = Depends(get_current_user)):
    try:
        # Update profile in 'profiles' table
        data = {}
        if update_data.username:
            data["username"] = update_data.username
            
        if update_data.avatar_emoji:
            # Validate emoji is in allowed list
            ALLOWED_EMOJIS = [
                '😀', '😃', '😄', '😎', '🤓', '🥳', '🤩', '😊', '🤗', '🤔',
                '🐶', '🐱', '🐼', '🐯', '🦁', '🐸', '🦊', '🦉', '🐔', '🐵',
                '🎮', '🎯', '🎲', '⚡', '🔥', '💎', '🏆', '🌟', '⭐', '👾'
            ]
            if update_data.avatar_emoji not in ALLOWED_EMOJIS:
                raise HTTPException(status_code=400, detail="Invalid emoji selected")
            data["avatar_emoji"] = update_data.avatar_emoji
            
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

@router.get("/{identifier}/public_profile", operation_id="get_public_profile")
def get_public_profile(identifier: str, current_user = Depends(get_current_user)):
    try:
        # Determine if identifier is UUID or username
        # Try UUID format first
        user_id = None
        try:
            # Simple UUID validation - check if it's in UUID format
            import uuid
            uuid.UUID(identifier)
            user_id = identifier  # It's a valid UUID
        except ValueError:
            # Not a UUID, treat as username
            username_lookup = supabase.table("profiles").select("id").eq("username", identifier).single().execute()
            if username_lookup.data:
                user_id = username_lookup.data['id']
        
        if not user_id:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Fetch Profile - select specific columns to avoid missing column errors
        response = supabase.table("profiles").select(
            "id, username, level, email, avatar_emoji, overall_win_count, total_xp_earned, daily_win_count, overall_win_rate, completed_tasks"
        ).eq("id", user_id).single().execute()
        profile = response.data
        
        if not profile:
            raise HTTPException(status_code=404, detail="User not found")

        # Check if following
        is_following = False
        follow_check = supabase.table("follows").select("created_at")\
            .eq("follower_id", current_user.id)\
            .eq("following_id", user_id)\
            .execute()
        if follow_check.data:
            is_following = True

        # Fetch Match History (Last 5 battles)
        battles_res = supabase.table("battles").select("*")\
            .or_(f"user1_id.eq.{user_id},user2_id.eq.{user_id}")\
            .eq("status", "completed")\
            .order("end_date", desc=True)\
            .limit(5)\
            .execute()
            
        match_history = battles_res.data

        # Enrich match history with rival names
        enriched_history = []
        for battle in match_history:
            rival_id = battle['user2_id'] if battle['user1_id'] == user_id else battle['user1_id']
            rival_res = supabase.table("profiles").select("username").eq("id", rival_id).single().execute()
            rival_name = rival_res.data['username'] if rival_res.data else "Unknown"
            
            result = "DRAW"
            if battle.get('winner_id') == user_id:
                result = "WIN"
            elif battle.get('winner_id') == rival_id:
                result = "LOSS"
                
            enriched_history.append({
                "id": battle['id'],
                "date": battle['end_date'],
                "rival": rival_name,
                "result": result,
                "duration": battle.get('duration', 5)
            })

        return {
            "id": profile['id'],
            "username": profile['username'],
            "level": profile['level'],
            "avatar_url": None,  # Column doesn't exist yet
            "avatar_emoji": profile.get('avatar_emoji', '😀'),  # Default to smiley
            "is_following": is_following,
            "stats": {
                "battle_wins": profile.get("overall_win_count", 0),
                "total_xp": profile.get("total_xp_earned", 0),
                "rounds_won": profile.get("daily_win_count", 0),
                "win_rate": f"{profile.get('overall_win_rate', 0)}%",
                "tasks_completed": profile.get("completed_tasks", 0)
            },
            "match_history": enriched_history
        }

    except Exception as e:
        print(f"Public profile error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


