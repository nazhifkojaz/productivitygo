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
from utils.logging_config import get_logger
from utils.query_columns import PROFILE_PRIVATE, BATTLE_MATCH_HISTORY, PROFILE_TIMEZONE, ADVENTURE_MATCH_HISTORY
from utils.profile_helpers import batch_fetch_rival_usernames, enrich_battle_history
from database import async_retry_on_connection_error

router = APIRouter(prefix="/users", tags=["users"])
logger = get_logger(__name__)

class UserUpdate(BaseModel):
    username: Optional[str] = None
    avatar_url: Optional[str] = None
    avatar_emoji: Optional[str] = None
    timezone: Optional[str] = None

from dependencies import get_current_user

@router.put("/profile", operation_id="update_profile")
async def update_profile(update_data: UserUpdate, user = Depends(get_current_user)):
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
        response = await supabase.table("profiles").update(data).eq("id", user.id).execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/profile", operation_id="get_profile")
async def get_profile(user = Depends(get_current_user)):
    try:
        # Fetch Profile
        response = await supabase.table("profiles").select(PROFILE_PRIVATE).eq("id", user.id).single().execute()
        profile = response.data

        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")

        # Calculate Stats from Battles
        battle_count = profile.get('battle_count', 0)
        battle_win_count = profile.get('battle_win_count', 0)

        # REFACTOR-002: Use shared win rate calculation
        win_rate_str = format_win_rate(battle_win_count, battle_count)

        # Calculate rank
        level = profile.get('level', 1)
        rank = calculate_rank(level, battle_count, battle_win_count)

        # Adventure stats from PROFILE_PRIVATE (Feature 3)
        adventure_count = profile.get("adventure_count", 0)
        monster_defeats = profile.get("monster_defeats", 0)

        profile["stats"] = {
            # PvP stats
            "battle_wins": battle_win_count,
            "total_xp": profile.get("total_xp_earned", 0),
            "battle_fought": battle_count,
            "win_rate": win_rate_str,
            "tasks_completed": profile.get("completed_tasks", 0),

            # Adventure stats (Feature 3)
            "monster_rating": profile.get("monster_rating", 0),
            "monster_defeats": monster_defeats,
            "monster_escapes": profile.get("monster_escapes", 0),
            "adventure_count": adventure_count,
            "highest_tier_reached": profile.get("highest_tier_reached", "easy"),
            "total_damage_dealt": profile.get("total_damage_dealt", 0),

            # Derived stats (Feature 3)
            "adventure_completion_rate": format_win_rate(monster_defeats, adventure_count),
            "avg_damage_per_adventure": (
                profile.get("total_damage_dealt", 0) // adventure_count
            ) if adventure_count > 0 else 0,
        }
        profile["rank"] = rank

        # Fetch Match History (Last 10 battles - completed only for now)
        battles_res = await supabase.table("battles").select(BATTLE_MATCH_HISTORY)\
            .or_(f"user1_id.eq.{user.id},user2_id.eq.{user.id}")\
            .eq("status", "completed")\
            .order("end_date", desc=True)\
            .limit(10)\
            .execute()

        match_history = battles_res.data

        # REFACTOR-007: Use centralized rival batch-fetch and enrichment
        rivals_map = await batch_fetch_rival_usernames(match_history, user.id)
        enriched_history = enrich_battle_history(match_history, user.id, rivals_map, include_type=True)

        # Fetch Adventure History (Last 10 completed/escaped adventures)
        adventures_res = await supabase.table("adventures").select(ADVENTURE_MATCH_HISTORY)\
            .eq("user_id", user.id)\
            .in_("status", ["completed", "escaped"])\
            .order("completed_at", desc=True)\
            .limit(10)\
            .execute()

        adventure_history = adventures_res.data

        # Batch fetch monsters for adventure history
        monster_ids = [adv.get('monster_id') for adv in adventure_history if adv.get('monster_id')]
        monsters_map = {}
        if monster_ids:
            monsters_res = await supabase.table("monsters").select("id, name, emoji, tier").in_("id", list(set(monster_ids))).execute()
            monsters_map = {m['id']: m for m in monsters_res.data}

        # Enrich adventure history
        enriched_adventures = []
        for adventure in adventure_history:
            monster = monsters_map.get(adventure.get('monster_id'), {})

            # Determine result based on status and damage
            if adventure.get('status') == 'escaped':
                result = "ESCAPED"
            elif adventure.get('monster_current_hp', 0) <= 0:
                result = "WIN"
            else:
                result = "COMPLETED"

            enriched_adventures.append({
                "id": adventure['id'],
                "date": adventure.get('completed_at'),
                "rival": monster.get('name', 'Unknown Monster'),
                "emoji": monster.get('emoji', '👾'),
                "result": result,
                "duration": adventure.get('duration', 5),
                "xp_earned": adventure.get('xp_earned', 0),
                "type": "adventure"
            })

        # Combine battle and adventure history, sorted by date
        combined_history = enriched_history + enriched_adventures
        combined_history.sort(key=lambda x: x.get('date', ''), reverse=True)
        combined_history = combined_history[:15]  # Limit to 15 total entries

        profile["match_history"] = combined_history

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
        profile = await supabase.table("profiles").select(
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

    @async_retry_on_connection_error(max_retries=3, delay=0.3)
    async def fetch_profile_data(user_id: str):
        """Fetch profile with retry on connection errors"""
        return await supabase.table("profiles").select(
            "id, username, level, email, avatar_emoji, battle_win_count, total_xp_earned, "
            "battle_count, completed_tasks, adventure_count, monster_defeats, "
            "monster_escapes, monster_rating, highest_tier_reached, total_damage_dealt, "
            "created_at"
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
            username_lookup = await supabase.table("profiles").select("id").eq("username", identifier).single().execute()
            if username_lookup.data:
                user_id = username_lookup.data['id']

        if not user_id:
            raise HTTPException(status_code=404, detail="User not found")

        # Fetch Profile with retry logic
        response = await fetch_profile_data(user_id)
        profile = response.data

        if not profile:
            raise HTTPException(status_code=404, detail="User not found")

        # Check if current user follows this profile
        is_following = False
        follow_check = await supabase.table("follows").select("follower_id").eq("follower_id", current_user.id).eq("following_id", user_id).execute()
        if follow_check.data:
            is_following = True

        # REFACTOR-002: Use shared win rate calculation
        battle_count = profile.get('battle_count', 0)
        battle_win_count = profile.get('battle_win_count', 0)
        win_rate_str = format_win_rate(battle_win_count, battle_count)

        # Adventure stats (Feature 3)
        adventure_count = profile.get('adventure_count', 0)
        monster_defeats = profile.get('monster_defeats', 0)

        # Calculate rank
        level = profile.get('level', 1)
        rank = calculate_rank(level, battle_count, battle_win_count)

        # Fetch Match History (Last 5 battles)
        battles_res = await supabase.table("battles").select(BATTLE_MATCH_HISTORY)\
            .or_(f"user1_id.eq.{user_id},user2_id.eq.{user_id}")\
            .eq("status", "completed")\
            .order("end_date", desc=True)\
            .limit(5)\
            .execute()

        match_history = battles_res.data

        # REFACTOR-007: Use centralized rival batch-fetch and enrichment
        # Note: include_type=False because public profile only shows battles
        rivals_map = await batch_fetch_rival_usernames(match_history, user_id)
        enriched_history = enrich_battle_history(match_history, user_id, rivals_map, include_type=False)

        return {
            "id": profile['id'],
            "username": profile['username'],
            "level": profile['level'],
            "rank": rank,
            "avatar_emoji": profile.get('avatar_emoji', '😀'),  # Default to smiley
            "is_following": is_following,
            "stats": {
                # PvP stats
                "battle_wins": battle_win_count,
                "total_xp": profile.get('total_xp_earned', 0),
                "battle_fought": battle_count,
                "win_rate": win_rate_str,
                "tasks_completed": profile.get("completed_tasks", 0),

                # Adventure stats (Feature 3)
                "monster_rating": profile.get("monster_rating", 0),
                "monster_defeats": monster_defeats,
                "monster_escapes": profile.get("monster_escapes", 0),
                "adventure_count": adventure_count,
                "highest_tier_reached": profile.get("highest_tier_reached", "easy"),
                "total_damage_dealt": profile.get("total_damage_dealt", 0),

                # Derived stats (Feature 3)
                "adventure_completion_rate": format_win_rate(monster_defeats, adventure_count),
                "avg_damage_per_adventure": (
                    profile.get("total_damage_dealt", 0) // adventure_count
                ) if adventure_count > 0 else 0,
            },
            "created_at": profile.get("created_at"),
            "match_history": enriched_history
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Public profile error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
