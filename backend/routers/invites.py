from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from database import supabase
from dependencies import get_current_user
from services.battle_service import BattleService
from utils.query_columns import BATTLE_FOR_REMATCH, BATTLE_PENDING_CHECK

router = APIRouter(prefix="/invites", tags=["invites"])


class InviteRequest(BaseModel):
    rival_id: str    # User UUID
    start_date: str  # YYYY-MM-DD
    duration: int    # 3-5 days


@router.get("/pending", operation_id="get_invites")
async def get_pending_invites(user = Depends(get_current_user)):
    """
    Get pending battle invites for the current user.
    Returns battles where user is the invitee (user2) with status 'pending'.
    """
    # Find pending battles where user is the invitee (user2)
    # We assume user1 is always the inviter for now
    res = await supabase.table("battles").select("*, user1:profiles!user1_id(username)")\
        .eq("user2_id", user.id)\
        .eq("status", "pending")\
        .execute()
    return res.data


@router.post("/send", operation_id="invite_user")
async def send_invite(invite: InviteRequest, user = Depends(get_current_user)):
    """
    Create a new battle invite.
    """
    battle = await BattleService.create_invite(user.id, invite.rival_id, invite.start_date, invite.duration)
    return {"status": "success", "battle": battle}


@router.post("/{battle_id}/accept", operation_id="accept_battle")
async def accept_battle_invite(battle_id: str, user = Depends(get_current_user)):
    """
    Accept a pending battle invite.
    """
    await BattleService.accept_invite(battle_id, user.id)
    # Fetch updated battle to return
    battle_res = await supabase.table("battles").select("*").eq("id", battle_id).single().execute()
    return battle_res.data


@router.post("/{battle_id}/reject", operation_id="reject_battle")
async def reject_battle_invite(battle_id: str, user = Depends(get_current_user)):
    """
    Reject or cancel a battle invite.
    """
    return await BattleService.reject_invite(battle_id, user.id)


@router.post("/{battle_id}/rematch", operation_id="rematch_battle")
async def create_rematch(battle_id: str, user = Depends(get_current_user)):
    """
    Create a rematch invitation after a completed battle.
    """
    return await BattleService.create_rematch(battle_id, user.id)


@router.get("/{battle_id}/pending-rematch", operation_id="get_pending_rematch")
async def get_pending_rematch(battle_id: str, user = Depends(get_current_user)):
    """
    Check if there's a pending rematch invitation for a given completed battle.
    """
    # Get the completed battle to find users
    completed_battle_res = await supabase.table("battles").select(BATTLE_FOR_REMATCH).eq("id", battle_id).execute()
    if not completed_battle_res.data:
        raise HTTPException(status_code=404, detail="Battle not found")

    completed_battle = completed_battle_res.data[0]
    user1_id = completed_battle['user1_id']
    user2_id = completed_battle['user2_id']

    # Find pending rematch battles between the same users in either order:
    # (user1_id=ALICE AND user2_id=BOB) OR (user1_id=BOB AND user2_id=ALICE)
    matching_res = await supabase.table("battles").select(BATTLE_PENDING_CHECK)\
        .eq("status", "pending")\
        .or_(f"and(user1_id.eq.{user1_id},user2_id.eq.{user2_id}),and(user1_id.eq.{user2_id},user2_id.eq.{user1_id})")\
        .execute()

    if matching_res.data:
        # Take the most recent one
        pending = max(matching_res.data, key=lambda b: b['created_at'])
        requester_id = pending['user1_id']
        return {
            "exists": True,
            "battle_id": pending['id'],
            "requester_id": requester_id,
            "is_requester": requester_id == user.id
        }
    else:
        return {"exists": False}


@router.post("/{battle_id}/decline", operation_id="decline_rematch")
async def decline_rematch(battle_id: str, user = Depends(get_current_user)):
    """
    Decline a pending rematch invitation.
    """
    return await BattleService.decline_rematch(battle_id)
