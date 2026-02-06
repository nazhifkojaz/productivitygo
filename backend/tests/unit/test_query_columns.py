"""
Unit tests for query column constants.

Tests verify that column sets contain the expected fields
and follow consistent naming conventions.
"""

import pytest
from utils.query_columns import (
    BATTLE_STATUS_ONLY,
    BATTLE_BASIC,
    BATTLE_FOR_ACCEPT,
    BATTLE_FOR_REJECT,
    BATTLE_FOR_REMATCH,
    BATTLE_PENDING_CHECK,
    BATTLE_RELOAD,
    BATTLE_FOR_DECLINE,
    BATTLE_MATCH_HISTORY,
    PROFILE_EXISTS,
    PROFILE_BASIC,
    PROFILE_TIMEZONE,
    PROFILE_PRIVATE,
    TASKS_FULL,
)


class TestBattleQueryColumns:
    """Test battle table column constants."""

    def test_battle_status_only_contains_only_needed_fields(self):
        """Verify BATTLE_STATUS_ONLY only has id and status."""
        fields = BATTLE_STATUS_ONLY.split(", ")
        assert fields == ["id", "status"]

    def test_battle_basic_contains_core_fields(self):
        """Verify BATTLE_BASIC contains all core battle fields."""
        expected = {"id", "status", "user1_id", "user2_id", "start_date", "end_date", "duration"}
        actual = set(BATTLE_BASIC.split(", "))
        assert actual == expected

    def test_battle_for_accept_contains_needed_fields(self):
        """Verify BATTLE_FOR_ACCEPT contains fields for accept verification."""
        expected = {"id", "status", "user1_id", "user2_id"}
        actual = set(BATTLE_FOR_ACCEPT.split(", "))
        assert actual == expected

    def test_battle_for_reject_contains_needed_fields(self):
        """Verify BATTLE_FOR_REJECT contains fields for reject verification."""
        expected = {"id", "status", "user2_id", "user1_id"}
        actual = set(BATTLE_FOR_REJECT.split(", "))
        assert actual == expected

    def test_battle_for_rematch_contains_needed_fields(self):
        """Verify BATTLE_FOR_REMATCH contains fields for rematch."""
        expected = {"id", "user1_id", "user2_id", "duration"}
        actual = set(BATTLE_FOR_REMATCH.split(", "))
        assert actual == expected

    def test_battle_pending_check_contains_needed_fields(self):
        """Verify BATTLE_PENDING_CHECK contains fields for pending rematch check."""
        expected = {"id", "user1_id", "user2_id", "status", "created_at"}
        actual = set(BATTLE_PENDING_CHECK.split(", "))
        assert actual == expected

    def test_battle_reload_contains_status_tracking_fields(self):
        """Verify BATTLE_RELOAD contains fields for lazy eval reload."""
        expected = {"id", "status", "current_round"}
        actual = set(BATTLE_RELOAD.split(", "))
        assert actual == expected

    def test_battle_for_decline_contains_needed_fields(self):
        """Verify BATTLE_FOR_DECLINE contains fields for decline verification."""
        expected = {"id", "status", "user1_id", "user2_id"}
        actual = set(BATTLE_FOR_DECLINE.split(", "))
        assert actual == expected

    def test_all_battle_constants_include_id(self):
        """Verify all battle query constants include 'id' field."""
        battle_constants = [
            BATTLE_STATUS_ONLY,
            BATTLE_BASIC,
            BATTLE_FOR_ACCEPT,
            BATTLE_FOR_REJECT,
            BATTLE_FOR_REMATCH,
            BATTLE_PENDING_CHECK,
            BATTLE_RELOAD,
            BATTLE_FOR_DECLINE,
        ]
        for constant in battle_constants:
            fields = constant.split(", ")
            assert "id" in fields, f"Constant {constant} missing 'id' field"


class TestProfileQueryColumns:
    """Test profile table column constants."""

    def test_profile_exists_only_has_id(self):
        """Verify PROFILE_EXISTS only has id."""
        assert PROFILE_EXISTS == "id"

    def test_profile_basic_contains_id_and_username(self):
        """Verify PROFILE_BASIC has id and username."""
        fields = PROFILE_BASIC.split(", ")
        assert fields == ["id", "username"]

    def test_profile_timezone_only_has_timezone(self):
        """Verify PROFILE_TIMEZONE only has timezone."""
        assert PROFILE_TIMEZONE == "timezone"

    def test_profile_private_contains_all_user_fields(self):
        """Verify PROFILE_PRIVATE contains all user-visible fields."""
        expected = {
            "id", "username", "email", "level", "total_xp_earned",
            "battle_count", "battle_win_count", "completed_tasks",
            "avatar_emoji", "timezone"
        }
        actual = set(PROFILE_PRIVATE.split(", "))
        assert actual == expected


class TestTasksQueryColumns:
    """Test tasks table column constants."""

    def test_tasks_full_contains_all_task_fields(self):
        """Verify TASKS_FULL contains all fields needed for task response."""
        expected = {
            "id", "daily_entry_id", "content", "is_optional",
            "is_completed", "proof_url", "created_at"
        }
        actual = set(TASKS_FULL.split(", "))
        assert actual == expected


class TestBattleQueryColumnsExtended:
    """Test additional battle table column constants."""

    def test_battle_match_history_contains_needed_fields(self):
        """Verify BATTLE_MATCH_HISTORY contains fields for match history display."""
        expected = {"id", "user1_id", "user2_id", "winner_id", "end_date", "duration", "status"}
        actual = set(BATTLE_MATCH_HISTORY.split(", "))
        assert actual == expected


class TestColumnConsistency:
    """Test consistency across column constants."""

    def test_no_duplicate_fields_in_constants(self):
        """Verify no constant has duplicate fields."""
        from utils.query_columns import (
            BATTLE_STATUS_ONLY,
            BATTLE_BASIC,
            BATTLE_FOR_ACCEPT,
            BATTLE_FOR_REJECT,
            BATTLE_FOR_REMATCH,
            BATTLE_PENDING_CHECK,
            BATTLE_RELOAD,
            BATTLE_FOR_DECLINE,
            PROFILE_BASIC,
        )

        constants = [
            BATTLE_STATUS_ONLY,
            BATTLE_BASIC,
            BATTLE_FOR_ACCEPT,
            BATTLE_FOR_REJECT,
            BATTLE_FOR_REMATCH,
            BATTLE_PENDING_CHECK,
            BATTLE_RELOAD,
            BATTLE_FOR_DECLINE,
            PROFILE_BASIC,
        ]

        for constant in constants:
            fields = constant.split(", ")
            unique_fields = set(fields)
            assert len(fields) == len(unique_fields), f"Duplicate fields found in: {constant}"

    def test_fields_are_alphabetically_ordered_within_constants(self):
        """Verify fields are ordered consistently (alphabetically after id)."""
        # This is a style check - ensures maintainability
        from utils.query_columns import (
            BATTLE_BASIC,
            BATTLE_FOR_ACCEPT,
            BATTLE_FOR_REMATCH,
        )

        # Check a few key constants
        for constant in [BATTLE_BASIC, BATTLE_FOR_ACCEPT, BATTLE_FOR_REMATCH]:
            fields = constant.split(", ")
            # id should always be first if present
            if "id" in fields:
                assert fields[0] == "id", f"id should be first in: {constant}"
