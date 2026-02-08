"""
Async Integration Tests — verify no unawaited coroutines or sync/async mismatches.

Each test sends a real HTTP request through:
    httpx.AsyncClient -> ASGITransport -> FastAPI ASGI -> async router -> mocked supabase

The supabase layer is mocked (no network), but everything above it is real.
"""
import asyncio
import warnings
import pytest
from unittest.mock import Mock, AsyncMock, patch

from tests.integration.conftest import ChainableMock
from utils.enums import GameMode


# =============================================================================
# Helpers
# =============================================================================

def _table_router(tables: dict):
    """
    Return a side_effect callable for ``supabase_mock.table`` that dispatches
    to per-table ChainableMocks configured by *tables* dict.

    Usage::

        patched_supabase.table.side_effect = _table_router({
            "profiles": profiles_mock,
            "battles": battles_mock,
        })
    """
    def _route(table_name):
        if table_name in tables:
            return tables[table_name]
        # Fallback: return a generic ChainableMock with empty data
        return ChainableMock()
    return _route


# =============================================================================
# Health / Root
# =============================================================================

class TestHealthEndpoints:

    async def test_root_returns_ok(self, async_client):
        resp = await async_client.get("/")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"

    async def test_health_returns_healthy(self, async_client):
        resp = await async_client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"


# =============================================================================
# Auth Flow
# =============================================================================

class TestAuthFlow:

    async def test_protected_endpoint_returns_401_without_auth(self, unauth_client):
        resp = await unauth_client.get("/api/battles/current")
        assert resp.status_code == 401

    async def test_protected_endpoint_works_with_auth(self, async_client, patched_supabase):
        """Auth override is in place; a 404 (no battle) proves auth passed."""
        patched_supabase.table.return_value.select.return_value \
            .or_.return_value.eq.return_value.execute = AsyncMock(
                return_value=Mock(data=[])
            )
        resp = await async_client.get("/api/battles/current")
        # 404 = "No active battle found" — means auth succeeded
        assert resp.status_code == 404


# =============================================================================
# Battles
# =============================================================================

class TestBattlesEndpoints:

    async def test_get_current_battle_404_when_none(self, async_client, patched_supabase):
        patched_supabase.table.return_value.select.return_value \
            .or_.return_value.eq.return_value.execute = AsyncMock(
                return_value=Mock(data=[])
            )
        resp = await async_client.get("/api/battles/current")
        assert resp.status_code == 404

    async def test_get_current_battle_returns_data(self, async_client, patched_supabase):
        # Mock matches: battles table (SELECT * + FK join to profiles)
        # Schema: battles(id, user1_id, user2_id, winner_id, status, duration,
        #   current_round, start_date, end_date, break_days_used, max_break_days,
        #   is_on_break, break_end_date, break_requested_by, break_request_expires_at,
        #   completed_at, created_at)
        battle = {
            "id": "battle-int-1",
            "user1_id": "test-user-id-123",
            "user2_id": "rival-456",
            "winner_id": None,
            "status": "active",
            "duration": 5,
            "current_round": 5,
            "start_date": "2026-03-01",
            "end_date": "2026-03-05",
            "break_days_used": 0,
            "max_break_days": 2,
            "is_on_break": False,
            "break_end_date": None,
            "break_requested_by": None,
            "break_request_expires_at": None,
            "completed_at": None,
            "created_at": "2026-02-28T00:00:00Z",
            # FK join: profiles!user1_id(username, level, timezone,
            #   battle_win_count, battle_count, total_xp_earned, completed_tasks)
            "user1": {
                "username": "Tester",
                "level": 3,
                "timezone": "UTC",
                "battle_win_count": 1,
                "battle_count": 2,
                "total_xp_earned": 500,
                "completed_tasks": 10,
            },
            "user2": {
                "username": "Rival",
                "level": 2,
                "timezone": "UTC",
                "battle_win_count": 0,
                "battle_count": 1,
                "total_xp_earned": 200,
                "completed_tasks": 5,
            },
        }

        battles_mock = ChainableMock()
        battles_mock.select.return_value.or_.return_value \
            .eq.return_value.execute = AsyncMock(return_value=Mock(data=[battle]))

        daily_entries_mock = ChainableMock()
        daily_entries_mock.select.return_value.eq.return_value \
            .eq.return_value.execute = AsyncMock(return_value=Mock(data=[]))

        patched_supabase.table.side_effect = _table_router({
            "battles": battles_mock,
            "daily_entries": daily_entries_mock,
        })

        # Patch process_battle_rounds at the utility module (imported inside function body)
        with patch("utils.battle_processor.process_battle_rounds", new_callable=AsyncMock, return_value=0):
            resp = await async_client.get("/api/battles/current")

        assert resp.status_code == 200
        body = resp.json()
        assert body["id"] == "battle-int-1"
        assert "app_state" in body

    async def test_forfeit_battle(self, async_client):
        with patch("routers.battles.BattleService") as svc:
            svc.forfeit_battle = AsyncMock(return_value={"status": "forfeited", "winner_id": "rival-456"})
            resp = await async_client.post("/api/battles/some-battle-id/forfeit")

        assert resp.status_code == 200
        assert resp.json()["status"] == "forfeited"


# =============================================================================
# Tasks
# =============================================================================

class TestTasksEndpoints:

    async def test_get_quota(self, async_client, patched_supabase):
        profiles_mock = ChainableMock()
        profiles_mock.select.return_value.eq.return_value \
            .single.return_value.execute = AsyncMock(
                return_value=Mock(data={"timezone": "UTC"})
            )
        patched_supabase.table.side_effect = _table_router({"profiles": profiles_mock})

        resp = await async_client.get("/api/tasks/quota")
        assert resp.status_code == 200
        body = resp.json()
        assert "date" in body
        assert "quota" in body

    async def test_get_today_tasks_empty(self, async_client, patched_supabase):
        profiles_mock = ChainableMock()
        profiles_mock.select.return_value.eq.return_value \
            .single.return_value.execute = AsyncMock(
                return_value=Mock(data={"timezone": "UTC"})
            )

        daily_entries_mock = ChainableMock()
        daily_entries_mock.select.return_value.eq.return_value \
            .eq.return_value.execute = AsyncMock(return_value=Mock(data=[]))

        patched_supabase.table.side_effect = _table_router({
            "profiles": profiles_mock,
            "daily_entries": daily_entries_mock,
        })

        resp = await async_client.get("/api/tasks/today")
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_complete_task(self, async_client, patched_supabase):
        task_data = {
            "id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
            "daily_entry_id": "11111111-2222-3333-4444-555555555555",
            "content": "Test task",
            "is_completed": True,
            "is_optional": False,
            "proof_url": None,
            "created_at": "2026-01-01T00:00:00Z",
        }

        tasks_mock = ChainableMock()
        tasks_mock.update.return_value.eq.return_value.execute = AsyncMock(
            return_value=Mock(data=[task_data])
        )
        patched_supabase.table.side_effect = _table_router({"tasks": tasks_mock})

        resp = await async_client.post(
            "/api/tasks/aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee/complete"
        )
        assert resp.status_code == 200
        assert resp.json()["task"]["is_completed"] is True

    async def test_draft_tasks(self, async_client, patched_supabase):
        profiles_mock = ChainableMock()
        profiles_mock.select.return_value.eq.return_value \
            .single.return_value.execute = AsyncMock(
                return_value=Mock(data={"timezone": "UTC"})
            )

        daily_entries_mock = ChainableMock()
        daily_entries_mock.select.return_value.eq.return_value \
            .eq.return_value.execute = AsyncMock(return_value=Mock(data=[]))
        daily_entries_mock.insert.return_value.execute = AsyncMock(
            return_value=Mock(data=[{"id": "new-entry-id"}])
        )

        tasks_mock = ChainableMock()
        tasks_mock.insert.return_value.execute = AsyncMock(
            return_value=Mock(data=[])
        )

        patched_supabase.table.side_effect = _table_router({
            "profiles": profiles_mock,
            "daily_entries": daily_entries_mock,
            "tasks": tasks_mock,
        })

        with patch(
            "routers.tasks.get_active_game_session",
            new_callable=AsyncMock,
            return_value=("battle-xyz", GameMode.PVP),
        ):
            resp = await async_client.post(
                "/api/tasks/draft",
                json=[
                    {"content": "Task 1", "is_optional": False},
                    {"content": "Task 2", "is_optional": False},
                    {"content": "Task 3", "is_optional": False},
                ],
            )

        assert resp.status_code == 200
        assert resp.json()["status"] == "success"


# =============================================================================
# Invites
# =============================================================================

class TestInvitesEndpoints:

    async def test_get_pending_invites(self, async_client, patched_supabase):
        patched_supabase.table.return_value.select.return_value \
            .eq.return_value.eq.return_value.execute = AsyncMock(
                return_value=Mock(data=[])
            )
        resp = await async_client.get("/api/invites/pending")
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_send_invite(self, async_client):
        # Return from BattleService.create_invite -> battles table INSERT result
        mock_battle = {
            "id": "new-battle-1",
            "user1_id": "test-user-id-123",
            "user2_id": "rival-789",
            "winner_id": None,
            "status": "pending",
            "duration": 5,
            "current_round": 0,
            "start_date": "2026-04-01",
            "end_date": "2026-04-05",
            "break_days_used": 0,
            "max_break_days": 2,
            "is_on_break": False,
            "break_end_date": None,
            "break_requested_by": None,
            "break_request_expires_at": None,
            "completed_at": None,
            "created_at": "2026-03-30T00:00:00Z",
        }
        with patch("routers.invites.BattleService") as svc:
            svc.create_invite = AsyncMock(return_value=mock_battle)
            resp = await async_client.post(
                "/api/invites/send",
                json={
                    "rival_id": "rival-789",
                    "start_date": "2026-04-01",
                    "duration": 5,
                },
            )
        assert resp.status_code == 200
        assert resp.json()["battle"]["id"] == "new-battle-1"

    async def test_accept_invite(self, async_client, patched_supabase):
        with patch("routers.invites.BattleService") as svc:
            svc.accept_invite = AsyncMock(return_value=None)

            # Mock matches: battles table SELECT * after accept
            patched_supabase.table.return_value.select.return_value \
                .eq.return_value.single.return_value.execute = AsyncMock(
                    return_value=Mock(data={
                        "id": "battle-accept-1",
                        "user1_id": "inviter",
                        "user2_id": "test-user-id-123",
                        "winner_id": None,
                        "status": "active",
                        "duration": 5,
                        "current_round": 0,
                        "start_date": "2026-04-01",
                        "end_date": "2026-04-05",
                        "break_days_used": 0,
                        "max_break_days": 2,
                        "is_on_break": False,
                        "break_end_date": None,
                        "break_requested_by": None,
                        "break_request_expires_at": None,
                        "completed_at": None,
                        "created_at": "2026-03-30T00:00:00Z",
                    })
                )

            resp = await async_client.post("/api/invites/battle-accept-1/accept")

        assert resp.status_code == 200
        assert resp.json()["status"] == "active"


# =============================================================================
# Adventures
# =============================================================================

class TestAdventuresEndpoints:

    async def test_get_monster_pool(self, async_client, patched_supabase):
        profiles_mock = ChainableMock()
        profiles_mock.select.return_value.eq.return_value \
            .single.return_value.execute = AsyncMock(
                return_value=Mock(data={"monster_rating": 0})
            )
        patched_supabase.table.side_effect = _table_router({"profiles": profiles_mock})

        with patch("routers.adventures.AdventureService") as svc:
            svc.initialize_refresh_count = AsyncMock(return_value=3)
            svc.get_weighted_monster_pool = AsyncMock(return_value=[
                {"id": "m1", "name": "Slime", "tier": "easy", "base_hp": 100},
            ])
            svc.get_unlocked_tiers = Mock(return_value=["easy"])

            resp = await async_client.get("/api/adventures/monsters")

        assert resp.status_code == 200
        body = resp.json()
        assert "monsters" in body
        assert body["refreshes_remaining"] == 3

    async def test_start_adventure(self, async_client, patched_supabase):
        # Mock matches: ADVENTURE_WITH_MONSTER =
        #   "*, monster:monsters(id, name, emoji, tier, base_hp, description)"
        # Schema: adventures(id, user_id, monster_id, duration, start_date,
        #   deadline, monster_max_hp, monster_current_hp, status, current_round,
        #   total_damage_dealt, xp_earned, break_days_used, max_break_days,
        #   is_on_break, break_end_date, created_at, completed_at)
        adventure_data = {
            "id": "adv-1",
            "user_id": "test-user-id-123",
            "monster_id": "m1",
            "duration": 5,
            "start_date": "2026-03-01",
            "deadline": "2026-03-05",
            "monster_max_hp": 100,
            "monster_current_hp": 100,
            "status": "active",
            "current_round": 0,
            "total_damage_dealt": 0,
            "xp_earned": 0,
            "break_days_used": 0,
            "max_break_days": 2,
            "is_on_break": False,
            "break_end_date": None,
            "created_at": "2026-02-28T00:00:00Z",
            "completed_at": None,
            # FK join: monsters(id, name, emoji, tier, base_hp, description)
            "monster": {
                "id": "m1",
                "name": "Lazy Slime",
                "emoji": "🟢",
                "tier": "easy",
                "base_hp": 100,
                "description": "Just five more minutes...",
            },
        }
        with patch("routers.adventures.AdventureService") as svc:
            svc.create_adventure = AsyncMock(return_value={"id": "adv-1"})

            patched_supabase.table.return_value.select.return_value \
                .eq.return_value.single.return_value.execute = AsyncMock(
                    return_value=Mock(data=adventure_data)
                )

            resp = await async_client.post(
                "/api/adventures/start",
                json={"monster_id": "m1"},
            )

        assert resp.status_code == 200
        assert resp.json()["id"] == "adv-1"

    async def test_get_current_adventure_404(self, async_client, patched_supabase):
        # Simulate .single() raising when no row found
        patched_supabase.table.return_value.select.return_value \
            .eq.return_value.eq.return_value \
            .single.return_value.execute = AsyncMock(
                side_effect=Exception("No rows found")
            )

        resp = await async_client.get("/api/adventures/current")
        assert resp.status_code == 404


# =============================================================================
# Users
# =============================================================================

class TestUsersEndpoints:

    async def test_get_profile(self, async_client, patched_supabase):
        # Mock matches: PROFILE_PRIVATE = "id, username, email, level,
        #   total_xp_earned, battle_count, battle_win_count,
        #   completed_tasks, avatar_emoji, timezone"
        profile_data = {
            "id": "test-user-id-123",
            "username": "Tester",
            "email": "tester@example.com",
            "level": 5,
            "total_xp_earned": 2500,
            "battle_count": 10,
            "battle_win_count": 3,
            "completed_tasks": 45,
            "avatar_emoji": "😎",
            "timezone": "UTC",
        }

        profiles_mock = ChainableMock()
        profiles_mock.select.return_value.eq.return_value \
            .single.return_value.execute = AsyncMock(
                return_value=Mock(data=profile_data)
            )

        # Battles for match history
        battles_mock = ChainableMock()
        battles_mock.select.return_value.or_.return_value \
            .eq.return_value.order.return_value \
            .limit.return_value.execute = AsyncMock(
                return_value=Mock(data=[])
            )

        # Adventures for match history
        adventures_mock = ChainableMock()
        adventures_mock.select.return_value.eq.return_value \
            .in_.return_value.order.return_value \
            .limit.return_value.execute = AsyncMock(
                return_value=Mock(data=[])
            )

        patched_supabase.table.side_effect = _table_router({
            "profiles": profiles_mock,
            "battles": battles_mock,
            "adventures": adventures_mock,
        })

        resp = await async_client.get("/api/users/profile")
        assert resp.status_code == 200
        body = resp.json()
        assert body["username"] == "Tester"
        assert "stats" in body
        assert "rank" in body
        assert "match_history" in body

    async def test_update_profile(self, async_client, patched_supabase):
        patched_supabase.table.return_value.update.return_value \
            .eq.return_value.execute = AsyncMock(
                return_value=Mock(data=[{"username": "NewName"}])
            )

        resp = await async_client.put(
            "/api/users/profile",
            json={"username": "NewName"},
        )
        assert resp.status_code == 200

    async def test_get_rank_info(self, async_client, patched_supabase):
        profiles_mock = ChainableMock()
        profiles_mock.select.return_value.eq.return_value \
            .single.return_value.execute = AsyncMock(
                return_value=Mock(data={
                    "level": 5,
                    "total_xp_earned": 2500,
                    "battle_count": 10,
                    "battle_win_count": 3,
                })
            )
        patched_supabase.table.side_effect = _table_router({"profiles": profiles_mock})

        resp = await async_client.get("/api/users/rank-info")
        assert resp.status_code == 200
        body = resp.json()
        assert "rank" in body
        assert "level" in body
        assert "xp_progress" in body


# =============================================================================
# Social
# =============================================================================

class TestSocialEndpoints:

    async def test_follow_user(self, async_client, patched_supabase):
        profiles_mock = ChainableMock()
        profiles_mock.select.return_value.eq.return_value.execute = AsyncMock(
            return_value=Mock(data=[{"id": "other-user-id"}])
        )

        follows_mock = ChainableMock()
        follows_mock.insert.return_value.execute = AsyncMock(
            return_value=Mock(data=[])
        )

        patched_supabase.table.side_effect = _table_router({
            "profiles": profiles_mock,
            "follows": follows_mock,
        })

        resp = await async_client.post("/api/social/follow/other-user-id")
        assert resp.status_code == 200
        assert "message" in resp.json()

    async def test_get_following(self, async_client, patched_supabase):
        follows_mock = ChainableMock()
        follows_mock.select.return_value.eq.return_value.execute = AsyncMock(
            return_value=Mock(data=[])
        )
        patched_supabase.table.side_effect = _table_router({"follows": follows_mock})

        resp = await async_client.get("/api/social/following")
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_search_users(self, async_client, patched_supabase):
        profiles_mock = ChainableMock()
        profiles_mock.select.return_value.ilike.return_value \
            .neq.return_value.limit.return_value.execute = AsyncMock(
                return_value=Mock(data=[
                    {
                        "id": "found-user",
                        "username": "FoundUser",
                        "level": 2,
                        "total_xp_earned": 100,
                        "battle_win_count": 0,
                        "battle_count": 0,
                        "avatar_emoji": "😀",
                    }
                ])
            )
        patched_supabase.table.side_effect = _table_router({"profiles": profiles_mock})

        resp = await async_client.get("/api/social/search?q=Found")
        assert resp.status_code == 200
        body = resp.json()
        assert len(body) == 1
        assert body[0]["username"] == "FoundUser"


# =============================================================================
# Async Pipeline Integrity
# =============================================================================

class TestAsyncPipelineIntegrity:

    async def test_no_unawaited_coroutine_warnings(self, async_client, patched_supabase):
        """Verify no RuntimeWarning about unawaited coroutines during a request."""
        patched_supabase.table.return_value.select.return_value \
            .or_.return_value.eq.return_value.execute = AsyncMock(
                return_value=Mock(data=[])
            )

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            await async_client.get("/api/battles/current")

        coroutine_warnings = [
            w for w in caught
            if issubclass(w.category, RuntimeWarning)
            and "coroutine" in str(w.message).lower()
        ]
        assert coroutine_warnings == [], (
            f"Unawaited coroutine warnings: {[str(w.message) for w in coroutine_warnings]}"
        )

    async def test_concurrent_requests_no_shared_state_leak(self, async_client, patched_supabase):
        """Fire 5 concurrent requests and verify no errors from shared state."""
        patched_supabase.table.return_value.select.return_value \
            .or_.return_value.eq.return_value.execute = AsyncMock(
                return_value=Mock(data=[])
            )
        patched_supabase.table.return_value.select.return_value \
            .eq.return_value.single.return_value.execute = AsyncMock(
                return_value=Mock(data={"timezone": "UTC"})
            )
        patched_supabase.table.return_value.select.return_value \
            .eq.return_value.eq.return_value.execute = AsyncMock(
                return_value=Mock(data=[])
            )

        requests = [
            async_client.get("/api/battles/current"),
            async_client.get("/api/tasks/quota"),
            async_client.get("/api/invites/pending"),
            async_client.get("/api/social/following"),
            async_client.get("/health"),
        ]

        responses = await asyncio.gather(*requests, return_exceptions=True)

        for i, resp in enumerate(responses):
            assert not isinstance(resp, Exception), (
                f"Request {i} raised: {resp}"
            )
            # Each should return a valid HTTP status (not a 500 from async corruption)
            assert resp.status_code in (200, 404), (
                f"Request {i} returned unexpected {resp.status_code}: {resp.text}"
            )
