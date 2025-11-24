from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from database import supabase
from dependencies import get_current_user

router = APIRouter(prefix="/social", tags=["social"])

class UserProfile(BaseModel):
    id: str
    username: str
    level: int
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
        print(f"Follow error: {e}")
        return {"message": "Already following"}

@router.delete("/unfollow/{user_id}", response_model=FollowResponse)
def unfollow_user(user_id: str, current_user = Depends(get_current_user)):
    try:
        supabase.table("follows").delete().eq("follower_id", current_user.id).eq("following_id", user_id).execute()
        return {"message": "Unfollowed successfully"}
    except Exception as e:
        print(f"Unfollow error: {e}")
        raise HTTPException(status_code=500, detail="Failed to unfollow")

@router.get("/following", response_model=List[UserProfile])
def get_following(current_user = Depends(get_current_user)):
    # Get IDs of users I follow
    follows = supabase.table("follows").select("following_id").eq("follower_id", current_user.id).execute()
    if not follows.data:
        return []
    
    following_ids = [f['following_id'] for f in follows.data]
    
    # Get profiles - select * to avoid column specification issues
    profiles = supabase.table("profiles").select("*").in_("id", following_ids).execute()
    
    # Build response with only needed fields
    result = []
    for profile in profiles.data:
        result.append({
            'id': profile['id'],
            'username': profile.get('username', 'Unknown'),
            'level': profile.get('level', 1),
            'avatar_url': None,
            'avatar_emoji': profile.get('avatar_emoji', '😀')
        })
    
    return result

@router.get("/followers", response_model=List[UserProfile])
def get_followers(current_user = Depends(get_current_user)):
    # Get IDs of users following me
    followers = supabase.table("follows").select("follower_id").eq("following_id", current_user.id).execute()
    if not followers.data:
        return []
    
    follower_ids = [f['follower_id'] for f in followers.data]
    
    # Get profiles - select * to avoid column specification issues
    profiles = supabase.table("profiles").select("*").in_("id", follower_ids).execute()
    
    # Build response with only needed fields
    result = []
    for profile in profiles.data:
        result.append({
            'id': profile['id'],
            'username': profile.get('username', 'Unknown'),
            'level': profile.get('level', 1),
            'avatar_url': None,
            'avatar_emoji': profile.get('avatar_emoji', '😀')
        })
    
    return result

@router.get("/search", response_model=List[UserProfile])
def search_users(q: str, current_user = Depends(get_current_user)):
    if not q or len(q) < 2:
        return []
    
    # Search by username, exclude self - select * to avoid column issues
    profiles = supabase.table("profiles").select("*")\
        .ilike("username", f"%{q}%")\
        .neq("id", current_user.id)\
        .limit(10)\
        .execute()
        
    # Build response with only needed fields
    result = []
    for profile in profiles.data:
        result.append({
            'id': profile['id'],
            'username': profile.get('username', 'Unknown'),
            'level': profile.get('level', 1),
            'avatar_url': None,
            'avatar_emoji': profile.get('avatar_emoji', '😀')
        })
        
    return result
