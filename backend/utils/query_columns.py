"""
Reusable column sets for Supabase queries to avoid over-fetching.

This module defines column constants for common query patterns.
Using specific columns instead of select("*") reduces data transfer
and makes queries self-documenting.
"""

# =============================================================================
# Battle Table Columns
# =============================================================================

# For checking if a battle exists and its status
BATTLE_STATUS_ONLY = "id, status"

# For basic battle information (user IDs, dates, duration)
BATTLE_BASIC = "id, status, user1_id, user2_id, start_date, end_date, duration"

# For accepting battles - need to verify ownership
BATTLE_FOR_ACCEPT = "id, status, user1_id, user2_id"

# For rejecting invites - need to verify user is invitee or inviter
BATTLE_FOR_REJECT = "id, status, user2_id, user1_id"

# For rematch operations - need user IDs and duration
BATTLE_FOR_REMATCH = "id, user1_id, user2_id, duration"

# For checking pending rematches - need IDs, status, and creation time
BATTLE_PENDING_CHECK = "id, user1_id, user2_id, status, created_at"

# For reloading battle after lazy evaluation - need status tracking
BATTLE_RELOAD = "id, status, current_round"

# For decline rematch - need to verify battle status
BATTLE_FOR_DECLINE = "id, status, user1_id, user2_id"

# =============================================================================
# Profile Table Columns
# =============================================================================

# For checking if a user/profile exists
PROFILE_EXISTS = "id"

# For basic profile lookup (username display)
PROFILE_BASIC = "id, username"

# For timezone-based date calculations
PROFILE_TIMEZONE = "timezone"

# For private profile endpoint (all user-visible fields)
PROFILE_PRIVATE = "id, username, email, level, total_xp_earned, battle_count, battle_win_count, completed_tasks, avatar_emoji, timezone"

# =============================================================================
# Tasks Table Columns
# =============================================================================

# For fetching tasks (all fields needed for response)
TASKS_FULL = "id, daily_entry_id, content, is_optional, assigned_score, is_completed, proof_url, created_at"

# =============================================================================
# Battle Table Columns (Additions)
# =============================================================================

# For match history display
BATTLE_MATCH_HISTORY = "id, user1_id, user2_id, winner_id, end_date, duration, status"
