from datetime import date, timedelta, datetime
import pytz
from fastapi import HTTPException
from database import supabase
from utils.logging_config import get_logger
from utils.query_columns import (
    BATTLE_STATUS_ONLY,
    BATTLE_BASIC,
    BATTLE_FOR_ACCEPT,
    BATTLE_FOR_REJECT,
    BATTLE_FOR_REMATCH,
    BATTLE_PENDING_CHECK,
    BATTLE_FOR_DECLINE,
    PROFILE_EXISTS,
    PROFILE_BASIC,
)

logger = get_logger(__name__)

class BattleService:
    @staticmethod
    def create_invite(user_id: str, rival_id: str, start_date_str: str, duration: int):
        # 1. Validate Rival ID exists
        rival_res = supabase.table("profiles").select(PROFILE_BASIC).eq("id", rival_id).single().execute()
        if not rival_res.data:
            raise HTTPException(status_code=404, detail="User not found")
        
        if rival_id == user_id:
            raise HTTPException(status_code=400, detail="Cannot battle yourself")
            
        # 2. Check if either user is already in a battle (active or pending)
        # Check for user
        existing = supabase.table("battles").select(BATTLE_STATUS_ONLY)\
            .or_(f"user1_id.eq.{user_id},user2_id.eq.{user_id}")\
            .in_("status", ["active", "pending"])\
            .execute()

        if existing.data:
            raise HTTPException(status_code=400, detail="You are already in a battle or have a pending invite")

        # Check for rival
        rival_existing = supabase.table("battles").select(BATTLE_STATUS_ONLY)\
            .or_(f"user1_id.eq.{rival_id},user2_id.eq.{rival_id}")\
            .in_("status", ["active", "pending"])\
            .execute()
            
        if rival_existing.data:
            raise HTTPException(status_code=400, detail="Rival is already in a battle")
        
        # 3. Validate Date and Duration
        try:
            start_date = date.fromisoformat(start_date_str)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start date format")
            
        today = date.today()
        if start_date <= today:
            raise HTTPException(status_code=400, detail="Start date must be at least tomorrow")
            
        if duration < 3 or duration > 5:
            raise HTTPException(status_code=400, detail="Duration must be between 3 and 5 days")
            
        # Calculate end date (start + duration - 1)
        end_date = start_date + timedelta(days=duration - 1)
        
        # 4. Create Battle (Pending)
        battle_data = {
            "user1_id": user_id, # Inviter
            "user2_id": rival_id, # Invitee
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "duration": duration,
            "current_round": 0,
            "status": "pending"
        }
        
        res = supabase.table("battles").insert(battle_data).execute()
        return res.data[0]

    @staticmethod
    def accept_invite(battle_id: str, user_id: str):
        # BUG-005 FIX: Use atomic SQL function for accepting battles
        # This ensures battle status and both profile updates happen atomically
        try:
            result = supabase.rpc("accept_battle_atomic", {
                "battle_uuid": battle_id,
                "accepting_user": user_id
            }).execute()

            if result.data:
                data = result.data[0] if isinstance(result.data, list) else result.data
                success = data.get('success', False)
                error_message = data.get('error_message')

                if not success:
                    # Map SQL error messages to appropriate HTTP exceptions
                    if 'not found' in (error_message or '').lower():
                        raise HTTPException(status_code=404, detail="Battle not found")
                    elif 'not your invite' in (error_message or '').lower():
                        raise HTTPException(status_code=403, detail="Not your invite to accept")
                    elif 'not pending' in (error_message or '').lower():
                        raise HTTPException(status_code=400, detail="Invite not pending")
                    else:
                        raise HTTPException(status_code=500, detail=f"Failed to accept battle: {error_message}")

                # Fetch and return the updated battle
                battle_res = supabase.table("battles").select(BATTLE_FOR_ACCEPT).eq("id", battle_id).single().execute()
                return battle_res.data
            else:
                raise HTTPException(status_code=500, detail="Failed to accept battle")

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error accepting battle: {str(e)}")

    @staticmethod
    def reject_invite(battle_id: str, user_id: str):
        # Verify user is the invitee OR inviter (can cancel own invite)
        battle_res = supabase.table("battles").select(BATTLE_FOR_REJECT).eq("id", battle_id).single().execute()
        if not battle_res.data:
            raise HTTPException(status_code=404, detail="Battle not found")
            
        battle = battle_res.data
        if battle['user2_id'] != user_id and battle['user1_id'] != user_id:
            raise HTTPException(status_code=403, detail="Not your invite")
            
        # Delete the battle/invite
        supabase.table("battles").delete().eq("id", battle_id).execute()
        return {"status": "rejected"}

    @staticmethod
    def forfeit_battle(battle_id: str, user_id: str):
        # BUG-005 FIX: Use atomic SQL function for forfeiting battles
        # This prevents race conditions and ensures all stats are updated atomically
        try:
            result = supabase.rpc("forfeit_battle_atomic", {
                "battle_uuid": battle_id,
                "forfeiting_user": user_id
            }).execute()

            if result.data:
                data = result.data[0] if isinstance(result.data, list) else result.data
                winner_id = data.get('winner_id')
                already_completed = data.get('already_completed', False)

                if winner_id is None and not already_completed:
                    # SQL function raised an exception
                    raise HTTPException(status_code=500, detail="Failed to forfeit battle")

                if already_completed:
                    # Battle was already completed, return appropriate response
                    raise HTTPException(status_code=400, detail="Battle is already completed")

                return {"status": "forfeited", "winner_id": winner_id}
            else:
                raise HTTPException(status_code=500, detail="Failed to forfeit battle")

        except HTTPException:
            raise
        except Exception as e:
            # Check for specific SQL error messages
            error_str = str(e).lower()
            if 'not found' in error_str:
                raise HTTPException(status_code=404, detail="Battle not found")
            elif 'only forfeit active' in error_str or 'not a participant' in error_str:
                raise HTTPException(status_code=400, detail=str(e))
            else:
                raise HTTPException(status_code=500, detail=f"Error forfeiting battle: {str(e)}")

    @staticmethod
    def complete_battle(battle_id: str):
        # 1. Verify Battle
        battle_res = supabase.table("battles").select(BATTLE_STATUS_ONLY).eq("id", battle_id).execute()
        if not battle_res.data:
            raise HTTPException(status_code=404, detail="Battle not found")

        battle = battle_res.data[0]

        # Allow both 'active' and 'completed' statuses for idempotency
        # If already completed, the SQL function will handle it idempotently
        if battle['status'] not in ('active', 'completed'):
            raise HTTPException(status_code=400, detail="Battle is not active")

        # 2. Call database function to complete battle (now idempotent)
        try:
            result = supabase.rpc("complete_battle", {"battle_uuid": battle_id}).execute()
            if result.data:
                data = result.data[0] if isinstance(result.data, list) else result.data
                already_completed = data.get('already_completed', False)

                # Log idempotent calls for monitoring
                if already_completed:
                    logger.info(f"Battle {battle_id} was already completed, returning existing result (idempotent call)")

                return {
                    "status": "completed",
                    "winner_id": data.get('winner_id'),
                    "scores": {
                        "user1_total_xp": data.get('user1_total_xp'),
                        "user2_total_xp": data.get('user2_total_xp')
                    },
                    "already_completed": already_completed  # Indicates if this was an idempotent call
                }
            else:
                raise HTTPException(status_code=500, detail="Failed to complete battle")
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error completing battle: {str(e)}")

    @staticmethod
    def calculate_round(battle_id: str, round_date_str: str = None):
        # 1. Verify Battle
        battle_res = supabase.table("battles").select(BATTLE_STATUS_ONLY).eq("id", battle_id).execute()
        if not battle_res.data:
            raise HTTPException(status_code=404, detail="Battle not found")
            
        battle = battle_res.data[0]
        if battle['status'] != 'active':
            raise HTTPException(status_code=400, detail="Battle is not active")
        
        # 2. Determine round date (default to today)
        if round_date_str:
            try:
                target_date = date.fromisoformat(round_date_str)
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

    @staticmethod
    def archive_battle(battle_id: str):
        # Verify battle exists
        battle_res = supabase.table("battles").select(PROFILE_EXISTS).eq("id", battle_id).execute()
        if not battle_res.data:
            raise HTTPException(status_code=404, detail="Battle not found")
            
        # Update status
        # NOTE: 'archived' status is not supported by DB constraint yet.
        # Workaround: DELETE the battle to remove it from view.
        supabase.table("battles").delete().eq("id", battle_id).execute()
        return {"status": "archived"}

    @staticmethod
    def create_rematch(battle_id: str, user_id: str):
        # 1. Get old battle to find opponent
        old_battle_res = supabase.table("battles").select(BATTLE_FOR_REMATCH).eq("id", battle_id).execute()
        if not old_battle_res.data:
            raise HTTPException(status_code=404, detail="Battle not found")
        old_battle = old_battle_res.data[0]

        opponent_id = old_battle['user2_id'] if old_battle['user1_id'] == user_id else old_battle['user1_id']

        # 2. Check if pending rematch already exists (server-side filtering - item 6.1)
        user1_id = old_battle['user1_id']
        user2_id = old_battle['user2_id']

        # Use OR clause for server-side filtering instead of loading all pending battles
        existing_pending = supabase.table("battles").select(BATTLE_PENDING_CHECK)\
            .eq("status", "pending")\
            .or_(f"and(user1_id.eq.{user1_id},user2_id.eq.{user2_id}),and(user1_id.eq.{user2_id},user2_id.eq.{user1_id})")\
            .limit(1)\
            .execute()

        if existing_pending.data:
            # Rematch already requested, just return it
            return {"status": "rematch_already_exists", "battle": existing_pending.data[0]}
        
        # 3. Create new battle (Pending)
        today = date.today()
        start_date = today + timedelta(days=1) # Starts tomorrow
        
        # Inherit duration (default to 5 if not set)
        duration = old_battle.get('duration', 5)
        end_date = start_date + timedelta(days=duration - 1)
        
        new_battle_data = {
            "user1_id": user_id,
            "user2_id": opponent_id,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "duration": duration,
            "current_round": 0,
            "status": "pending"
        }
        
        res = supabase.table("battles").insert(new_battle_data).execute()
        return {"status": "rematch_created", "battle": res.data[0]}

    @staticmethod
    def decline_rematch(battle_id: str):
        # Find the pending battle
        battle_res = supabase.table("battles").select(BATTLE_FOR_DECLINE).eq("id", battle_id).execute()
        if not battle_res.data:
            raise HTTPException(status_code=404, detail="Battle not found")
            
        battle = battle_res.data[0]
        
        # Verify it's pending
        if battle['status'] != 'pending':
            raise HTTPException(status_code=400, detail="Battle is not pending")
        
        # Delete the pending battle
        supabase.table("battles").delete().eq("id", battle_id).execute()
        return {"status": "declined"}
