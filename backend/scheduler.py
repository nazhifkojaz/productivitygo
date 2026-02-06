"""
Background Scheduler for Periodic Tasks

Uses APScheduler to run hourly checks on:
- Active battles (PVP)
- Active adventures (single player)

REFACTOR-007: Replaced print statements with centralized logging.
"""
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from database import supabase
from utils.battle_processor import process_battle_rounds
from utils.adventure_processor import process_adventure_rounds
from utils.logging_config import get_logger

logger = get_logger(__name__)


def process_active_battles():
    """
    Hourly job: Check all active battles and process rounds
    when both players have finished their day.
    """
    logger.info("Running hourly battle check")

    # 1. Fetch all active battles
    try:
        battles_res = supabase.table("battles").select("*").eq("status", "active").execute()
        battles = battles_res.data if battles_res.data else []
        logger.info(f"Found {len(battles)} active battles")
    except Exception as e:
        logger.error(f"Error fetching battles: {e}")
        return

    # 2. Process each battle using shared utility
    total_rounds = 0
    for battle in battles:
        try:
            rounds = process_battle_rounds(battle)
            total_rounds += rounds
        except Exception as e:
            logger.error(f"Error processing battle {battle['id']}: {e}")
            continue

    logger.info(f"Hourly check complete. Processed {total_rounds} round(s)")


def process_active_adventures():
    """
    Hourly job: Check all active adventures and process rounds.
    """
    logger.info("Running hourly adventure check")

    try:
        adventures_res = supabase.table("adventures")\
            .select("*, monster:monsters(*)")\
            .eq("status", "active").execute()
        adventures = adventures_res.data if adventures_res.data else []
        logger.info(f"Found {len(adventures)} active adventures")
    except Exception as e:
        logger.error(f"Error fetching adventures: {e}")
        return

    total_rounds = 0
    for adventure in adventures:
        try:
            rounds = process_adventure_rounds(adventure)
            total_rounds += rounds
        except Exception as e:
            logger.error(f"Error processing adventure {adventure['id']}: {e}")
            continue

    logger.info(f"Adventure check complete. Processed {total_rounds} round(s)")


# Initialize scheduler
scheduler = BackgroundScheduler()

def start_scheduler():
    """Start the background scheduler"""
    # Battle processing job
    scheduler.add_job(
        process_active_battles,
        trigger='cron',
        minute=0,
        id='process_battles',
        replace_existing=True
    )

    # Adventure processing job
    scheduler.add_job(
        process_active_adventures,
        trigger='cron',
        minute=0,
        id='process_adventures',
        replace_existing=True
    )

    scheduler.start()
    logger.info("Background scheduler started (hourly battle + adventure processing)")

def shutdown_scheduler():
    """Gracefully shut down the scheduler"""
    scheduler.shutdown()
    logger.info("Background scheduler stopped")
