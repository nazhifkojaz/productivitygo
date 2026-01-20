from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from database import supabase
from typing import Optional
from dependencies import get_current_user
from utils.rank_calculations import (
    calculate_rank,
    get_next_rank_requirements,
    get_xp_progress,
    calculate_level_from_xp
)
from utils.stats import format_win_rate

router = APIRouter(prefix="/users", tags=["users"])

class UserUpdate(BaseModel):
    username: Optional[str] = None
    avatar_url: Optional[str] = None
    avatar_emoji: Optional[str] = None
    timezone: Optional[str] = None

from dependencies import get_current_user

@router.put("/profile", operation_id="update_profile")
def update_profile(update_data: UserUpdate, user = Depends(get_current_user)):
    try:
        # Update profile in 'profiles' table
        data = {}
        if update_data.username:
            data["username"] = update_data.username
            
        if update_data.timezone:
            data["timezone"] = update_data.timezone
            
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

        # Use update instead of upsert to be safer and strictly scope to user.id
        # Upsert might create a new row if ID doesn't exist (which shouldn't happen for profile update),
        # but explicit update with eq() is safer to prevent accidental cross-user updates.
        response = supabase.table("profiles").update(data).eq("id", user.id).execute()
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

        battle_count = profile.get('battle_count', 0)
        battle_win_count = profile.get('battle_win_count', 0)

        # REFACTOR-002: Use shared win rate calculation
        win_rate_str = format_win_rate(battle_win_count, battle_count)

        # Calculate rank
        level = profile.get('level', 1)
        rank = calculate_rank(level, battle_count, battle_win_count)

        profile["stats"] = {
            "battle_wins": battle_win_count,
            "total_xp": profile.get("total_xp_earned", 0),
            "battle_fought": battle_count,
            "win_rate": win_rate_str,
            "tasks_completed": profile.get("completed_tasks", 0)
        }
        profile["rank"] = rank
        
        return profile
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rank-info", operation_id="get_rank_info")
async def get_rank_info(user = Depends(get_current_user)):
    """
    Get user's rank, level, XP progress, and rank-up requirements.
    """
    try:
        # Fetch user profile stats
        profile = supabase.table("profiles").select(
            "level, total_xp_earned, battle_count, battle_win_count"
        ).eq("id", user.id).single().execute()
        
        if not profile.data:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        data = profile.data
        total_xp = data.get('total_xp_earned', 0)
        battle_count = data.get('battle_count', 0)
        battle_win_count = data.get('battle_win_count', 0)
        
        # Calculate level from XP (in case stored level is stale)
        current_level = calculate_level_from_xp(total_xp)
        
        # Calculate rank based on level and battle stats
        rank = calculate_rank(current_level, battle_count, battle_win_count)
        
        # Get XP progress toward next level
        xp_progress = get_xp_progress(total_xp)
        
        # Get rank-up requirements
        rank_up_req = get_next_rank_requirements(
            rank, 
            current_level, 
            battle_count, 
            battle_win_count
        )
        
        return {
            "rank": rank,
            "level": current_level,
            "xp": total_xp,
            "xp_progress": xp_progress,
            "rank_up_requirements": rank_up_req
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{identifier}/public_profile", operation_id="get_public_profile")
async def get_public_profile(identifier: str, current_user = Depends(get_current_user)):
    """
    Get public profile by username or UUID with retry logic for connection stability.
    """
    from database import retry_on_connection_error
    
    @retry_on_connection_error(max_retries=3, delay=0.3)
    def fetch_profile_data(user_id: str):
        """Fetch profile with retry on connection errors"""
        return supabase.table("profiles").select(
            "id, username, level, email, avatar_emoji, battle_win_count, total_xp_earned, battle_count, completed_tasks"
        ).eq("id", user_id).single().execute()
    
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
        
        # Fetch Profile with retry logic
        response = fetch_profile_data(user_id)
        profile = response.data
        
        if not profile:
            raise HTTPException(status_code=404, detail="User not found")

        # Check if current user follows this profile
        is_following = False
        follow_check = supabase.table("follows").select("follower_id").eq("follower_id", current_user.id).eq("following_id", user_id).execute()
        if follow_check.data:
            is_following = True

        # REFACTOR-002: Use shared win rate calculation
        battle_count = profile.get('battle_count', 0)
        battle_win_count = profile.get('battle_win_count', 0)
        win_rate_str = format_win_rate(battle_win_count, battle_count)

        # Calculate rank
        level = profile.get('level', 1)
        rank = calculate_rank(level, battle_count, battle_win_count)

        # Fetch Match History (Last 5 battles)
        battles_res = supabase.table("battles").select("*")\
            .or_(f"user1_id.eq.{user_id},user2_id.eq.{user_id}")\
            .eq("status", "completed")\
            .order("end_date", desc=True)\
            .limit(5)\
            .execute()
            
        match_history = battles_res.data

        # Collect unique rival IDs
        rival_ids = set()
        for battle in match_history:
            rival_id = battle['user2_id'] if battle['user1_id'] == user_id else battle['user1_id']
            rival_ids.add(rival_id)

        # Batch fetch all rivals in single query (fixes N+1 issue)
        rivals_map = {}
        if rival_ids:
            rivals_res = supabase.table("profiles").select("id, username").in_("id", list(rival_ids)).execute()
            rivals_map = {r['id']: r['username'] for r in rivals_res.data}

        # Enrich match history with rival names
        enriched_history = []
        for battle in match_history:
            rival_id = battle['user2_id'] if battle['user1_id'] == user_id else battle['user1_id']
            rival_name = rivals_map.get(rival_id, "Unknown")
            
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
            "rank": rank,
            "avatar_emoji": profile.get('avatar_emoji', '😀'),  # Default to smiley
            "is_following": is_following,
            "stats": {
                "battle_wins": battle_win_count,
                "total_xp": profile.get('total_xp_earned', 0),
                "battle_fought": battle_count,
                "win_rate": win_rate_str,
                "tasks_completed": profile.get("completed_tasks", 0)
            },
            "match_history": enriched_history
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Public profile error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
