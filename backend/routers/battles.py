from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from datetime import date, timedelta, datetime
import pytz
from pydantic import BaseModel

from database import supabase
from dependencies import get_current_user
from services.battle_service import BattleService
from utils.rank_calculations import calculate_rank
from utils.quota import get_daily_quota
from utils.stats import format_win_rate
from utils.query_columns import BATTLE_FOR_REMATCH, BATTLE_RELOAD, BATTLE_PENDING_CHECK

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
    
    # OPTIMIZATION: Fetch battle AND related profiles in ONE query
    # We need timezone for logic, and stats for Rival Radar
    res = supabase.table("battles").select(
        "*, user1:profiles!user1_id(username, level, timezone, battle_win_count, battle_count, total_xp_earned, completed_tasks), user2:profiles!user2_id(username, level, timezone, battle_win_count, battle_count, total_xp_earned, completed_tasks)"
    ).or_(f"user1_id.eq.{user.id},user2_id.eq.{user.id}")\
    .eq("status", "active")\
    .execute()
        
    if not res.data:
        # Return 404 so frontend knows to show Lobby (IDLE state)
        raise HTTPException(status_code=404, detail="No active battle found")
    
    # Get the most relevant active battle
    # (Usually there's only one, but if multiple, take latest ending)
    battle = max(res.data, key=lambda b: b['end_date'])
    
    start_date = date.fromisoformat(battle['start_date'])
    end_date = date.fromisoformat(battle['end_date'])

    # --- LAZY EVALUATION TRIGGER (Backup) ---
    if battle['status'] == 'active':
        from utils.battle_processor import process_battle_rounds
        rounds_processed = process_battle_rounds(battle)
        if rounds_processed > 0:
            # Reload battle to get updated status/current_round
            # We need to reload with the same join if we want to be consistent,
            # but usually just reloading the battle row is enough for status check.
            # However, to keep 'battle' object consistent with embedded data, let's just update the fields we know changed.
            battle_reload = supabase.table("battles").select(BATTLE_RELOAD).eq("id", battle['id']).single().execute()
            if battle_reload.data:
                # Update only battle fields, keep embedded profiles
                battle.update(battle_reload.data)

    # Determine App State based on USER LOCAL TIME
    # We have the user's profile embedded in user1 or user2
    if battle['user1_id'] == user.id:
        user_profile = battle['user1']
        rival_profile = battle['user2']
        rival_id = battle['user2_id']
    else:
        user_profile = battle['user2']
        rival_profile = battle['user1']
        rival_id = battle['user1_id']

    # Handle None profiles (deleted users, database inconsistencies)
    if user_profile is None:
        print(f"[WARNING] User profile missing for battle {battle['id']}, user {user.id}")
        user_profile = {'timezone': 'UTC', 'username': 'Unknown', 'level': 1}

    if rival_profile is None:
        print(f"[WARNING] Rival profile missing for battle {battle['id']}, rival {rival_id}")
        # Default rival profile with safe defaults
        rival_profile = {
            'timezone': 'UTC',
            'username': 'Unknown Rival',
            'level': 1,
            'battle_win_count': 0,
            'battle_count': 0,
            'total_xp_earned': 0,
            'completed_tasks': 0
        }

    user_tz = user_profile.get('timezone', 'UTC')

    try:
        user_today = datetime.now(pytz.timezone(user_tz)).date()
    except pytz.exceptions.UnknownTimeZoneError:
        # Invalid timezone in profile, fall back to UTC
        user_today = datetime.now(pytz.utc).date()

    if battle['status'] == 'pending':
        app_state = 'PENDING_ACCEPTANCE'
    elif battle['status'] == 'completed':
        app_state = 'BATTLE_END'
    elif user_today < start_date:
        app_state = 'PRE_BATTLE'
    elif user_today > end_date:
        app_state = 'BATTLE_END'
    else:
        if user_today == end_date:
             app_state = 'LAST_BATTLE_DAY'
        else:
            app_state = 'IN_BATTLE'
        
    battle['app_state'] = app_state
    duration = battle.get('duration', 5)
    current_round = battle.get('current_round', 0)

    # --- LAZY EVALUATION TRIGGER (FAIR MODE) ---
    # Only process rounds when the date has passed for BOTH players.
    
    # 1. Get Timezones (Already fetched!)
    # Use 'or' to provide default dict if profile is None
    user1_data = battle['user1'] or {'timezone': 'UTC'}
    user2_data = battle['user2'] or {'timezone': 'UTC'}
    tz1 = user1_data.get('timezone', 'UTC')
    tz2 = user2_data.get('timezone', 'UTC')
    
    # 2. Helper to get local date
    def get_local_date(tz_str):
        """Get local date for timezone, falling back to UTC for invalid timezones."""
        try:
            return datetime.now(pytz.timezone(tz_str)).date()
        except pytz.exceptions.UnknownTimeZoneError:
            return datetime.now(pytz.utc).date()

    date1 = get_local_date(tz1)
    date2 = get_local_date(tz2)
    
    if battle['status'] == 'active':
        days_since_start = (user_today - start_date).days
        rounds_to_process = min(days_since_start, duration)
        
        if current_round < rounds_to_process:
            for r in range(current_round, rounds_to_process):
                round_date = start_date + timedelta(days=r)
                if date1 > round_date and date2 > round_date:
                    print(f"Processing round {r} (Date {round_date}) - Passed for both.")
                    try:
                        # BUG-004 FIX: Validate RPC response before incrementing round counter
                        rpc_result = supabase.rpc("calculate_daily_round", {
                            "battle_uuid": battle['id'],
                            "round_date": round_date.isoformat()
                        }).execute()

                        # Validate RPC succeeded before proceeding
                        if rpc_result.data is None:
                            print(f"Lazy Eval: RPC returned None for round {r}, stopping processing")
                            break

                        # Update round count only after validation
                        current_round += 1
                        supabase.table("battles").update({"current_round": current_round}).eq("id", battle['id']).execute()

                    except Exception as e:
                        print(f"Error in lazy evaluation for round {r}: {e}")
                        break
                else:
                    break
            
            battle['current_round'] = current_round

        if current_round >= duration:
            print("Lazy Eval: Battle finished, marking as completed")
            try:
                result = BattleService.complete_battle(battle['id'])
                if result:
                    battle['status'] = 'completed'
                    # Log if this was an idempotent call (already completed by another process)
                    if result.get('already_completed'):
                        print(f"Lazy Eval: Battle {battle['id']} was already completed by another process (safe idempotent call)")
            except Exception as e:
                 print(f"Error auto-completing battle: {e}")

    
    # Fetch Rival's Tasks for Today (Only if IN_BATTLE or LAST_BATTLE_DAY)
    # This still requires a separate fetch as it's a different table (daily_entries -> tasks)
    # We could optimize this too, but let's stick to the main profile optimization first.
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

        # REFACTOR-002: Use shared win rate calculation
        battle_win_count = rival_profile.get('battle_win_count', 0)
        battle_count = rival_profile.get('battle_count', 0)

        battle['rival'] = {
            'username': rival_profile.get('username', 'Unknown Rival'),
            'level': rival_profile.get('level', 1),
            'tasks_total': total_tasks,
            'tasks_completed': completed_tasks,
            'stats': {
                'battle_wins': battle_win_count,
                'battle_fought': battle_count,
                'level': rival_profile.get('level', 1),
                'total_xp': rival_profile.get('total_xp_earned', 0),
                'win_rate': format_win_rate(battle_win_count, battle_count),
                'tasks_completed': rival_profile.get('completed_tasks', 0)
            }
        }
    else:
        # REFACTOR-002: Use shared win rate calculation
        battle_win_count = rival_profile.get('battle_win_count', 0)
        battle_count = rival_profile.get('battle_count', 0)

        battle['rival'] = {
            'username': rival_profile.get('username', 'Unknown Rival'),
            'level': rival_profile.get('level', 1),
            'tasks_total': 0,
            'tasks_completed': 0,
            'stats': {
                'battle_wins': battle_win_count,
                'battle_fought': battle_count,
                'level': rival_profile.get('level', 1),
                'total_xp': rival_profile.get('total_xp_earned', 0),
                'win_rate': format_win_rate(battle_win_count, battle_count),
                'tasks_completed': rival_profile.get('completed_tasks', 0)
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
    """
    Create a new battle invite.
    """
    battle = BattleService.create_invite(user.id, invite.rival_id, invite.start_date, invite.duration)
    return {"status": "success", "battle": battle}


@router.post("/{battle_id}/accept", operation_id="accept_battle")
async def accept_battle(battle_id: str, user = Depends(get_current_user)):
    """
    Accept a pending battle invite.
    """
    BattleService.accept_invite(battle_id, user.id)
    # Fetch updated battle to return
    battle_res = supabase.table("battles").select("*").eq("id", battle_id).single().execute()
    return battle_res.data

@router.post("/{battle_id}/reject", operation_id="reject_battle")
async def reject_battle(battle_id: str, user = Depends(get_current_user)):
    """
    Reject or cancel a battle invite.
    """
    return BattleService.reject_invite(battle_id, user.id)

@router.post("/{battle_id}/forfeit", operation_id="forfeit_battle")
async def forfeit_battle(battle_id: str, user = Depends(get_current_user)):
    """
    Forfeit an active battle.
    """
    return BattleService.forfeit_battle(battle_id, user.id)

@router.post("/{battle_id}/leave", operation_id="leave_battle")
async def leave_battle(battle_id: str, user = Depends(get_current_user)):
    """
    Leave a battle result screen.
    """
    try:
        supabase.table("profiles").update({"current_battle": None}).eq("id", user.id).execute()
        return {"status": "left"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to leave battle: {str(e)}")

@router.post("/{battle_id}/complete", operation_id="complete_battle")
async def complete_battle(battle_id: str, user = Depends(get_current_user)):
    return BattleService.complete_battle(battle_id)

@router.post("/{battle_id}/daily-round", operation_id="calculate_daily_round")
async def calculate_round(battle_id: str, round_date: str = None, user = Depends(get_current_user)):
    """
    [DEBUG ONLY] Manually calculate daily round for a specific date.
    """
    from config import DEBUG_MODE
    if not DEBUG_MODE:
        raise HTTPException(status_code=404, detail="Endpoint not available in production mode")
    
    return BattleService.calculate_round(battle_id, round_date)


@router.get("/{battle_id}", operation_id="get_battle_details")
async def get_battle_details(battle_id: str, user = Depends(get_current_user)):
    # Fetch battle details including profiles
    # We need stats to calculate rank
    res = supabase.table("battles").select(
        "*, user1:profiles!user1_id(username, level, battle_count, battle_win_count), user2:profiles!user2_id(username, level, battle_count, battle_win_count)"
    ).eq("id", battle_id).execute()
        
    if not res.data:
        raise HTTPException(status_code=404, detail="Battle not found")
        
    battle = res.data[0]
    
    # Calculate Ranks
    if battle.get('user1'):
        u1 = battle['user1']
        u1['rank'] = calculate_rank(u1.get('level', 1), u1.get('battle_count', 0), u1.get('battle_win_count', 0))
        
    if battle.get('user2'):
        u2 = battle['user2']
        u2['rank'] = calculate_rank(u2.get('level', 1), u2.get('battle_count', 0), u2.get('battle_win_count', 0))
    
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
    return BattleService.archive_battle(battle_id)

@router.post("/{battle_id}/rematch", operation_id="rematch_battle")
async def rematch_battle(battle_id: str, user = Depends(get_current_user)):
    return BattleService.create_rematch(battle_id, user.id)

@router.get("/{battle_id}/pending-rematch", operation_id="get_pending_rematch")
async def get_pending_rematch(battle_id: str, user = Depends(get_current_user)):
    # Get the completed battle to find users
    completed_battle_res = supabase.table("battles").select(BATTLE_FOR_REMATCH).eq("id", battle_id).execute()
    if not completed_battle_res.data:
        raise HTTPException(status_code=404, detail="Battle not found")

    completed_battle = completed_battle_res.data[0]
    user1_id = completed_battle['user1_id']
    user2_id = completed_battle['user2_id']

    # REFACTOR-006: Use database-level filtering instead of fetching all pending battles
    # This query finds pending battles between the same users in either order:
    # (user1_id=ALICE AND user2_id=BOB) OR (user1_id=BOB AND user2_id=ALICE)
    matching_res = supabase.table("battles").select(BATTLE_PENDING_CHECK)\
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
    return BattleService.decline_rematch(battle_id)
