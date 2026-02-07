from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from database import supabase
from dependencies import get_current_user
from utils.logging_config import get_logger
from utils.rank_calculations import calculate_rank

router = APIRouter(prefix="/social", tags=["social"])
logger = get_logger(__name__)

class UserProfile(BaseModel):
    id: str
    username: str
    level: int
    rank: str = "Novice"
    avatar_url: Optional[str] = None
    avatar_emoji: Optional[str] = '😀'

class FollowResponse(BaseModel):
    message: str

@router.post("/follow/{user_id}", response_model=FollowResponse)
def follow_user(user_id: str, current_user = Depends(get_current_user)):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot follow yourself")

    # Check if user exists
    target_user = supabase.table("profiles").select("id").eq("id", user_id).execute()
    if not target_user.data:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        supabase.table("follows").insert({
            "follower_id": current_user.id,
            "following_id": user_id
        }).execute()
        return {"message": "Followed successfully"}
    except Exception as e:
        # Likely duplicate key error if already following
        logger.debug(f"Follow error: {e}")
        return {"message": "Already following"}

@router.delete("/unfollow/{user_id}", response_model=FollowResponse)
def unfollow_user(user_id: str, current_user = Depends(get_current_user)):
    try:
        supabase.table("follows").delete().eq("follower_id", current_user.id).eq("following_id", user_id).execute()
        return {"message": "Unfollowed successfully"}
    except Exception as e:
        logger.error(f"Unfollow error: {e}")
        raise HTTPException(status_code=500, detail="Failed to unfollow")

@router.get("/following", response_model=List[UserProfile])
def get_following(current_user = Depends(get_current_user)):
    from database import retry_on_connection_error
    
    @retry_on_connection_error(max_retries=3, delay=0.3)
    def fetch_following():
        # Get IDs of users I follow
        follows = supabase.table("follows").select("following_id").eq("follower_id", current_user.id).execute()
        if not follows.data:
            return []
        
        following_ids = [f['following_id'] for f in follows.data]
        
        # Get profiles with specific columns only
        profiles = supabase.table("profiles").select("id, username, level, total_xp_earned, battle_win_count, battle_count, avatar_emoji").in_("id", following_ids).execute()
        
        # Build response with only needed fields
        result = []
        for profile in profiles.data:
            level = profile.get('level', 1)
            result.append({
                'id': profile['id'],
                'username': profile.get('username', 'Unknown'),
                'level': level,
                'rank': calculate_rank(level, profile.get('battle_count', 0), profile.get('battle_win_count', 0)),
                'avatar_url': None,
                'avatar_emoji': profile.get('avatar_emoji', '😀')
            })

        return result

    try:
        return fetch_following()
    except Exception as e:
        logger.error(f"Error in get_following: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/followers", response_model=List[UserProfile])
def get_followers(current_user = Depends(get_current_user)):
    from database import retry_on_connection_error

    @retry_on_connection_error(max_retries=3, delay=0.3)
    def fetch_followers():
        # Get IDs of users following me
        followers = supabase.table("follows").select("follower_id").eq("following_id", current_user.id).execute()
        if not followers.data:
            return []

        follower_ids = [f['follower_id'] for f in followers.data]

        # Get profiles
        profiles = supabase.table("profiles").select("id, username, level, total_xp_earned, battle_win_count, battle_count, avatar_emoji").in_("id", follower_ids).execute()

        # Build response with only needed fields
        result = []
        for profile in profiles.data:
            level = profile.get('level', 1)
            result.append({
                'id': profile['id'],
                'username': profile.get('username', 'Unknown'),
                'level': level,
                'rank': calculate_rank(level, profile.get('battle_count', 0), profile.get('battle_win_count', 0)),
                'avatar_url': None,
                'avatar_emoji': profile.get('avatar_emoji', '😀')
            })

        return result

    try:
        return fetch_followers()
    except Exception as e:
        logger.error(f"Error in get_followers: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search", response_model=List[UserProfile])
def search_users(q: str, current_user = Depends(get_current_user)):
    if not q or len(q) < 2:
        return []
    
    # Search by username, exclude self - select * to avoid column issues
    profiles = supabase.table("profiles").select("id, username, level, total_xp_earned, battle_win_count, battle_count, avatar_emoji")\
        .ilike("username", f"%{q}%")\
        .neq("id", current_user.id)\
        .limit(10)\
        .execute()
        
    # Build response with only needed fields
    result = []
    for profile in profiles.data:
        level = profile.get('level', 1)
        result.append({
            'id': profile['id'],
            'username': profile.get('username', 'Unknown'),
            'level': level,
            'rank': calculate_rank(level, profile.get('battle_count', 0), profile.get('battle_win_count', 0)),
            'avatar_url': None,
            'avatar_emoji': profile.get('avatar_emoji', '😀')
        })

    return result
