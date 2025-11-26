"""
Background Scheduler for Periodic Tasks

Uses APScheduler to run hourly checks on active battles,
processing rounds when both players have completed their day.
"""
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from database import supabase
from utils.battle_processor import process_battle_rounds


def process_active_battles():
    """
    Hourly job: Check all active battles and process rounds
    when both players have finished their day.
    """
    print(f"[SCHEDULER] Running hourly battle check at {datetime.now()}")
    
    # 1. Fetch all active battles
    try:
        battles_res = supabase.table("battles").select("*").eq("status", "active").execute()
        battles = battles_res.data if battles_res.data else []
        print(f"[SCHEDULER] Found {len(battles)} active battles")
    except Exception as e:
        print(f"[SCHEDULER] Error fetching battles: {e}")
        return
    
    # 2. Process each battle using shared utility
    total_rounds = 0
    for battle in battles:
        try:
            rounds = process_battle_rounds(battle)
            total_rounds += rounds
        except Exception as e:
            print(f"[SCHEDULER] Error processing battle {battle['id']}: {e}")
            continue
    
    print(f"[SCHEDULER] Hourly check complete. Processed {total_rounds} round(s)")


# Initialize scheduler
scheduler = BackgroundScheduler()

def start_scheduler():
    """Start the background scheduler"""
    # Run every hour
    scheduler.add_job(
        process_active_battles,
        trigger='cron',
        minute=0,  # Run at the top of every hour
        id='process_battles',
        replace_existing=True
    )
    scheduler.start()
    print("[SCHEDULER] Background scheduler started (hourly)")

def shutdown_scheduler():
    """Gracefully shut down the scheduler"""
    scheduler.shutdown()
    print("[SCHEDULER] Background scheduler stopped")
