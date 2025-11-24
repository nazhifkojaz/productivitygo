from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from datetime import date, timedelta
from pydantic import BaseModel

from database import supabase
from dependencies import get_current_user

router = APIRouter(prefix="/battles", tags=["battles"])

class BattleInvite(BaseModel):
    rival_email: str

class BattleResponse(BaseModel):
    id: str
    user1_id: str
    user2_id: str
    status: str
    start_date: str
    end_date: str

@router.get("/current", operation_id="get_current_battle")
async def get_current_battle(user = Depends(get_current_user)):
    # Find ONLY active battles (NOT pending or completed)
    # Pending battles -> Handled in Lobby (UserDashboard)
    # Completed battles -> Handled in Battle Result
    res = supabase.table("battles").select("*")\
        .or_(f"user1_id.eq.{user.id},user2_id.eq.{user.id}")\
        .eq("status", "active")\
        .execute()
        
    if not res.data:
        # Return 404 so frontend knows to show Lobby (IDLE state)
        raise HTTPException(status_code=404, detail="No active battle found")
    
    # Get the most relevant active battle
    # (Usually there's only one, but if multiple, take latest ending)
    battle = max(res.data, key=lambda b: b['end_date'])
    
    # Determine App State
    today = date.today()
    start_date = date.fromisoformat(battle['start_date'])
    end_date = date.fromisoformat(battle['end_date'])
    
    if battle['status'] == 'pending':
        app_state = 'PENDING_ACCEPTANCE'
    elif battle['status'] == 'completed':
        app_state = 'BATTLE_END'
    elif today < start_date:
        app_state = 'PRE_BATTLE'
    elif today > end_date:
        app_state = 'BATTLE_END'
    else:
        # Use current_round and duration for precise state
        current_round = battle.get('current_round', 0)
        duration = battle.get('duration', 5)
        
        if current_round >= duration:
            app_state = 'LAST_BATTLE_DAY' # Or BATTLE_END if logic dictates, but usually LAST_BATTLE_DAY is for the final day itself
            # Actually, if current_round == duration, it means 5 rounds played? 
            # No, rounds_played starts at 0. 
            # If rounds_played == 5, battle is over.
            # Let's stick to date logic for LAST_BATTLE_DAY for now to be safe, 
            # but use rounds for progress display.
            if today == end_date:
                app_state = 'LAST_BATTLE_DAY'
            else:
                app_state = 'IN_BATTLE'
        elif today == end_date:
             app_state = 'LAST_BATTLE_DAY'
        else:
            app_state = 'IN_BATTLE'
        
    battle['app_state'] = app_state
    
    # Determine Rival ID
    rival_id = battle['user2_id'] if battle['user1_id'] == user.id else battle['user1_id']
    
    # Fetch Rival Profile
    rival_profile_res = supabase.table("profiles").select("*").eq("id", rival_id).execute()
    rival_data = rival_profile_res.data[0] if rival_profile_res.data else None
    
    # Fetch Rival's Tasks for Today (Only if IN_BATTLE or LAST_BATTLE_DAY)
    if app_state in ['IN_BATTLE', 'LAST_BATTLE_DAY']:
        today_str = date.today().isoformat()
        
        # 1. Get Daily Entry
        rival_entry_res = supabase.table("daily_entries").select("id")\
            .eq("user_id", rival_id)\
            .eq("date", today_str)\
            .execute()
            
        if rival_entry_res.data:
            entry_id = rival_entry_res.data[0]['id']
            # 2. Get Tasks
            rival_tasks_res = supabase.table("tasks").select("is_completed")\
                .eq("daily_entry_id", entry_id)\
                .execute()
            rival_tasks = rival_tasks_res.data
        else:
            rival_tasks = []
            
        total_tasks = len(rival_tasks)
        completed_tasks = sum(1 for t in rival_tasks if t['is_completed'])
        
        battle['rival'] = {
            'username': rival_data['username'] if rival_data else 'Unknown Rival',
            'level': rival_data['level'] if rival_data else 1,
            'tasks_total': total_tasks,
            'tasks_completed': completed_tasks,
            'stats': {
                'battle_wins': rival_data.get('overall_win_count', 0),
                'total_xp': rival_data.get('total_xp_earned', 0),
                'rounds_won': rival_data.get('daily_win_count', 0),
                'win_rate': f"{rival_data.get('overall_win_rate', 0)}%",
                'tasks_completed': rival_data.get('completed_tasks', 0)
            }
        }
    else:
         battle['rival'] = {
            'username': rival_data['username'] if rival_data else 'Unknown Rival',
            'level': rival_data['level'] if rival_data else 1,
            'tasks_total': 0,
            'tasks_completed': 0,
            'stats': {
                'battle_wins': rival_data.get('overall_win_count', 0) if rival_data else 0,
                'total_xp': rival_data.get('total_xp_earned', 0) if rival_data else 0,
                'rounds_won': rival_data.get('daily_win_count', 0) if rival_data else 0,
                'win_rate': f"{rival_data.get('overall_win_rate', 0)}%" if rival_data else "0%",
                'tasks_completed': rival_data.get('completed_tasks', 0) if rival_data else 0
            }
        }
    
    # Calculate Rounds Played
    rounds_res = supabase.table("daily_entries").select("id")\
        .eq("battle_id", battle['id'])\
        .eq("user_id", user.id)\
        .execute()
    battle['rounds_played'] = len(rounds_res.data)
        
    return battle

@router.get("/invites", operation_id="get_invites")
async def get_invites(user = Depends(get_current_user)):
    # Find pending battles where user is the invitee (user2)
    # We assume user1 is always the inviter for now
    res = supabase.table("battles").select("*, user1:profiles!user1_id(username)")\
        .eq("user2_id", user.id)\
        .eq("status", "pending")\
        .execute()
    return res.data

class InviteRequest(BaseModel):
    rival_id: str    # User UUID
    start_date: str  # YYYY-MM-DD
    duration: int    # 3-5 days

@router.post("/invite", operation_id="invite_user")
async def invite_user(invite: InviteRequest, user = Depends(get_current_user)):
    # 1. Validate Rival ID exists
    rival_res = supabase.table("profiles").select("id, username").eq("id", invite.rival_id).single().execute()
    if not rival_res.data:
        raise HTTPException(status_code=404, detail="User not found")
    
    rival_id = invite.rival_id
    
    if rival_id == user.id:
        raise HTTPException(status_code=400, detail="Cannot battle yourself")
        
    # 2. Check if either user is already in a battle (active or pending)
    # Check for user
    existing = supabase.table("battles").select("*")\
        .or_(f"user1_id.eq.{user.id},user2_id.eq.{user.id}")\
        .in_("status", ["active", "pending"])\
        .execute()
        
    if existing.data:
        raise HTTPException(status_code=400, detail="You are already in a battle or have a pending invite")

    # Check for rival
    rival_existing = supabase.table("battles").select("*")\
        .or_(f"user1_id.eq.{rival_id},user2_id.eq.{rival_id}")\
        .in_("status", ["active", "pending"])\
        .execute()
        
    if rival_existing.data:
        raise HTTPException(status_code=400, detail="Rival is already in a battle")
    
    # 3. Validate Date and Duration
    try:
        start_date = date.fromisoformat(invite.start_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid start date format")
        
    today = date.today()
    if start_date <= today:
        raise HTTPException(status_code=400, detail="Start date must be at least tomorrow")
        
    if invite.duration < 3 or invite.duration > 5:
        raise HTTPException(status_code=400, detail="Duration must be between 3 and 5 days")
        
    # Calculate end date (start + duration - 1)
    # e.g. Start Mon, Duration 3 -> Mon, Tue, Wed (End Wed)
    end_date = start_date + timedelta(days=invite.duration - 1)
    
    # 4. Create Battle (Pending)
    battle_data = {
        "user1_id": user.id, # Inviter
        "user2_id": rival_id, # Invitee
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "duration": invite.duration,
        "current_round": 0,
        "status": "pending"
    }
    
    res = supabase.table("battles").insert(battle_data).execute()
    
    return {"status": "success", "battle": res.data[0]}


@router.post("/{battle_id}/accept", operation_id="accept_battle")
async def accept_battle(battle_id: str, user = Depends(get_current_user)):
    # Verify user is the invitee
    battle_res = supabase.table("battles").select("*").eq("id", battle_id).single().execute()
    if not battle_res.data:
        raise HTTPException(status_code=404, detail="Battle not found")
        
    battle = battle_res.data
    if battle['user2_id'] != user.id:
        raise HTTPException(status_code=403, detail="Not your invite")
        
    if battle['status'] != 'pending':
        raise HTTPException(status_code=400, detail="Invite not pending")
        
    # Update status to active
    res = supabase.table("battles").update({"status": "active"}).eq("id", battle_id).execute()
    return res.data

@router.post("/{battle_id}/reject", operation_id="reject_battle")
async def reject_battle(battle_id: str, user = Depends(get_current_user)):
    # Verify user is the invitee OR inviter (can cancel own invite)
    battle_res = supabase.table("battles").select("*").eq("id", battle_id).single().execute()
    if not battle_res.data:
        raise HTTPException(status_code=404, detail="Battle not found")
        
    battle = battle_res.data
    if battle['user2_id'] != user.id and battle['user1_id'] != user.id:
        raise HTTPException(status_code=403, detail="Not your invite")
        
    # Delete the battle/invite
    supabase.table("battles").delete().eq("id", battle_id).execute()
    return {"status": "rejected"}

import hashlib

def get_daily_quota(date_obj: date) -> int:
    """Deterministically returns 3, 4, or 5 based on the date."""
    date_str = date_obj.isoformat()
    hash_obj = hashlib.md5(date_str.encode())
    hash_int = int(hash_obj.hexdigest(), 16)
    return (hash_int % 3) + 3

@router.post("/{battle_id}/complete", operation_id="complete_battle")
async def complete_battle(battle_id: str, user = Depends(get_current_user)):
    # 1. Verify Battle
    battle_res = supabase.table("battles").select("*").eq("id", battle_id).execute()
    if not battle_res.data:
        raise HTTPException(status_code=404, detail="Battle not found")
        
    battle = battle_res.data[0]
    if battle['status'] != 'active':
        raise HTTPException(status_code=400, detail="Battle is not active")
        
    # 2. Call database function to complete battle
    try:
        result = supabase.rpc("complete_battle", {"battle_uuid": battle_id}).execute()
        if result.data:
            data = result.data[0] if isinstance(result.data, list) else result.data
            return {
                "status": "completed",
                "winner_id": data.get('winner_id'),
                "scores": {
                    "user1_total_xp": data.get('user1_total_xp'),
                    "user2_total_xp": data.get('user2_total_xp')
                }
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to complete battle")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error completing battle: {str(e)}")

@router.post("/{battle_id}/daily-round", operation_id="calculate_daily_round")
async def calculate_round(battle_id: str, round_date: str = None, user = Depends(get_current_user)):
    """
    Calculate daily round for a specific date (for demo/testing).
    In production, this would be triggered automatically at end of day.
    """
    # 1. Verify Battle
    battle_res = supabase.table("battles").select("*").eq("id", battle_id).execute()
    if not battle_res.data:
        raise HTTPException(status_code=404, detail="Battle not found")
        
    battle = battle_res.data[0]
    if battle['status'] != 'active':
        raise HTTPException(status_code=400, detail="Battle is not active")
    
    # 2. Determine round date (default to today)
    if round_date:
        try:
            target_date = date.fromisoformat(round_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format (YYYY-MM-DD)")
    else:
        target_date = date.today()
    
    # 3. Call database function to calculate daily round
    try:
        result = supabase.rpc("calculate_daily_round", {
            "battle_uuid": battle_id,
            "round_date": target_date.isoformat()
        }).execute()
        
        if result.data:
            data = result.data[0] if isinstance(result.data, list) else result.data
            # Increment current_round
            current_round = battle.get('current_round', 0)
            supabase.table("battles").update({"current_round": current_round + 1}).eq("id", battle_id).execute()
            
            return {
                "status": "round_calculated",
                "date": target_date.isoformat(),
                "user1_xp": data.get('user1_xp'),
                "user2_xp": data.get('user2_xp'),
                "winner_id": data.get('winner_id')
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to calculate round")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating round: {str(e)}")

@router.get("/{battle_id}", operation_id="get_battle_details")
async def get_battle_details(battle_id: str, user = Depends(get_current_user)):
    # Fetch battle details including profiles
    res = supabase.table("battles").select("*, user1:profiles!user1_id(username, level), user2:profiles!user2_id(username, level)")\
        .eq("id", battle_id)\
        .execute()
        
    if not res.data:
        raise HTTPException(status_code=404, detail="Battle not found")
        
    battle = res.data[0]
    
    # Fetch Daily Breakdown
    entries_res = supabase.table("daily_entries").select("date, user_id, daily_xp")\
        .eq("battle_id", battle_id)\
        .order("date")\
        .execute()
        
    breakdown = {}
    user1_total = 0
    user2_total = 0
    
    if entries_res.data:
        for entry in entries_res.data:
            d = entry['date']
            uid = entry['user_id']
            xp = entry.get('daily_xp', 0) or 0
            
            if d not in breakdown:
                breakdown[d] = {'date': d, 'user1_xp': 0, 'user2_xp': 0}
                
            if uid == battle['user1_id']:
                breakdown[d]['user1_xp'] = xp
                user1_total += xp
            elif uid == battle['user2_id']:
                breakdown[d]['user2_xp'] = xp
                user2_total += xp
                
    # Determine daily winners
    daily_stats = []
    for d in sorted(breakdown.keys()):
        day_data = breakdown[d]
        u1 = day_data['user1_xp']
        u2 = day_data['user2_xp']
        winner = None
        if u1 > u2: winner = battle['user1_id']
        elif u2 > u1: winner = battle['user2_id']
        
        daily_stats.append({
            'date': d,
            'user1_xp': u1,
            'user2_xp': u2,
            'winner_id': winner
        })
        
    battle['daily_breakdown'] = daily_stats
    battle['scores'] = {
        'user1_xp': user1_total,
        'user2_xp': user2_total
    }
            
    return battle

@router.post("/{battle_id}/archive", operation_id="archive_battle")
async def archive_battle(battle_id: str, user = Depends(get_current_user)):
    # Verify user is in battle
    battle_res = supabase.table("battles").select("*").eq("id", battle_id).execute()
    if not battle_res.data:
        raise HTTPException(status_code=404, detail="Battle not found")
        
    # Update status
    # NOTE: 'archived' status is not supported by DB constraint yet.
    # Workaround: DELETE the battle to remove it from view.
    supabase.table("battles").delete().eq("id", battle_id).execute()
    return {"status": "archived"}

@router.post("/{battle_id}/rematch", operation_id="rematch_battle")
async def rematch_battle(battle_id: str, user = Depends(get_current_user)):
    # 1. Get old battle to find opponent
    old_battle_res = supabase.table("battles").select("*").eq("id", battle_id).execute()
    if not old_battle_res.data:
        raise HTTPException(status_code=404, detail="Battle not found")
    old_battle = old_battle_res.data[0]
    
    opponent_id = old_battle['user2_id'] if old_battle['user1_id'] == user.id else old_battle['user1_id']
    
    # 2. Check if pending rematch already exists
    all_pending = supabase.table("battles").select("*").eq("status", "pending").execute()
    user1_id = old_battle['user1_id']
    user2_id = old_battle['user2_id']
    
    existing_pending = [p for p in all_pending.data 
                        if (p['user1_id'] == user1_id and p['user2_id'] == user2_id) 
                        or (p['user1_id'] == user2_id and p['user2_id'] == user1_id)]
    
    if existing_pending:
        # Rematch already requested, just return it
        return {"status": "rematch_already_exists", "battle": existing_pending[0]}
    
    # 3. Create new battle (Pending)
    today = date.today()
    start_date = today + timedelta(days=1) # Starts tomorrow
    
    # Inherit duration (default to 5 if not set)
    duration = old_battle.get('duration', 5)
    end_date = start_date + timedelta(days=duration - 1)
    
    new_battle_data = {
        "user1_id": user.id,
        "user2_id": opponent_id,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "duration": duration,
        "current_round": 0,
        "status": "pending"
    }
    
    res = supabase.table("battles").insert(new_battle_data).execute()
    return {"status": "rematch_created", "battle": res.data[0]}

@router.get("/{battle_id}/pending-rematch", operation_id="get_pending_rematch")
async def get_pending_rematch(battle_id: str, user = Depends(get_current_user)):
    # Get the completed battle to find users
    completed_battle_res = supabase.table("battles").select("*").eq("id", battle_id).execute()
    if not completed_battle_res.data:
        raise HTTPException(status_code=404, detail="Battle not found")
    
    completed_battle = completed_battle_res.data[0]
    user1_id = completed_battle['user1_id']
    user2_id = completed_battle['user2_id']
    
    # Get all pending battles and filter in Python (PostgREST .or_() chaining doesn't work as expected)
    all_pending = supabase.table("battles").select("*").eq("status", "pending").execute()
    
    # Find pending battle between same users
    matching = [p for p in all_pending.data 
                if (p['user1_id'] == user1_id and p['user2_id'] == user2_id) 
                or (p['user1_id'] == user2_id and p['user2_id'] == user1_id)]
    
    if matching:
        # Take the most recent one
        pending = max(matching, key=lambda b: b['created_at'])
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
    # Find the pending battle
    battle_res = supabase.table("battles").select("*").eq("id", battle_id).execute()
    if not battle_res.data:
        raise HTTPException(status_code=404, detail="Battle not found")
        
    battle = battle_res.data[0]
    
    # Verify it's pending
    if battle['status'] != 'pending':
        raise HTTPException(status_code=400, detail="Battle is not pending")
    
    # Delete the pending battle
    supabase.table("battles").delete().eq("id", battle_id).execute()
    return {"status": "declined"}
