"""
Integration test fixtures for async endpoint testing.

Provides a real httpx.AsyncClient wired to the FastAPI ASGI app with
mocked Supabase at the module boundary — no real network calls, but the
full async request pipeline (httpx -> ASGI -> FastAPI -> router) is exercised.
"""
import pytest
import contextlib
from unittest.mock import Mock, MagicMock, AsyncMock, patch

import httpx

from dependencies import get_current_user


# ---------------------------------------------------------------------------
# ChainableMock — models the real Supabase client where builder methods
# (.table(), .select(), .eq(), .or_(), etc.) are sync, but .execute() is async.
# ---------------------------------------------------------------------------

class ChainableMock(MagicMock):
    """
    MagicMock subclass where every child is also a ChainableMock and
    .execute() at any depth is automatically an AsyncMock.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.execute = AsyncMock(return_value=Mock(data=[]))

    def _get_child_mock(self, /, **kw):
        return ChainableMock(**kw)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_user():
    """Mock authenticated user returned by the get_current_user dependency."""
    return Mock(id="test-user-id-123", email="integration@test.com")


@pytest.fixture
def supabase_mock():
    """
    A ChainableMock that behaves like the async Supabase client.

    - .table("x").select(...).eq(...).execute() -> awaitable
    - .auth.get_user(token) -> awaitable
    - .rpc("fn", params).execute() -> awaitable
    """
    mock = ChainableMock()

    # auth.get_user must be async
    mock.auth = Mock()
    mock.auth.get_user = AsyncMock(
        return_value=Mock(user=Mock(id="test-user-id-123"))
    )

    # rpc() should return a ChainableMock so .execute() is async
    mock.rpc = MagicMock(side_effect=lambda *a, **kw: ChainableMock())

    return mock


# All modules that import `supabase` from database.py at module level.
_SUPABASE_PATCH_TARGETS = [
    "database.supabase",
    "routers.battles.supabase",
    "routers.tasks.supabase",
    "routers.invites.supabase",
    "routers.users.supabase",
    "routers.social.supabase",
    "routers.adventures.supabase",
    "services.battle_service.supabase",
    "services.adventure_service.supabase",
    "utils.game_session.supabase",
    "utils.battle_processor.supabase",
    "utils.adventure_processor.supabase",
    "scheduler.supabase",
]


@pytest.fixture
def patched_supabase(supabase_mock):
    """
    Patch the supabase_mock into every module that imports supabase.

    Yields the single mock instance so tests can configure return values.
    """
    with contextlib.ExitStack() as stack:
        for target in _SUPABASE_PATCH_TARGETS:
            stack.enter_context(patch(target, supabase_mock))
        yield supabase_mock


@pytest.fixture
async def async_client(mock_user, patched_supabase):
    """
    httpx.AsyncClient wired to the FastAPI ASGI app.

    - Auth dependency overridden to return mock_user (no real token needed).
    - Startup hooks (init_supabase, init_db_pool, start_scheduler) are
      patched out so the app doesn't try to connect to real services.
    """
    from main import app

    # Override the auth dependency
    app.dependency_overrides[get_current_user] = lambda: mock_user

    # Prevent real initialization during startup events
    with patch("main.init_supabase", new_callable=AsyncMock), \
         patch("main.init_db_pool", new_callable=AsyncMock), \
         patch("main.start_scheduler"):

        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as client:
            yield client

    # Clean up overrides
    app.dependency_overrides.clear()


@pytest.fixture
async def unauth_client(patched_supabase):
    """
    httpx.AsyncClient WITHOUT auth override — for testing 401 responses.
    """
    from main import app

    # Make sure no leftover overrides
    app.dependency_overrides.pop(get_current_user, None)

    with patch("main.init_supabase", new_callable=AsyncMock), \
         patch("main.init_db_pool", new_callable=AsyncMock), \
         patch("main.start_scheduler"):

        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as client:
            yield client

    app.dependency_overrides.clear()
