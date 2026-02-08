"""
Unit tests for FastAPI main application.

Tests startup events and health check endpoints.
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient


@pytest.fixture
def mock_supabase_client():
    """
    Mock async Supabase client.

    The async client's table() method returns a regular (non-async) query builder.
    Only execute() is async.
    """
    mock = Mock()

    # Build the chain: table().select("count", count="exact").limit(1).execute()
    # The actual pattern in async supabase:
    # - table() returns a query builder (sync)
    # - select() returns a query builder (sync)
    # - count() returns a query builder (sync)
    # - limit() returns a query builder with execute() method
    # - execute() is async

    class AsyncQueryBuilder:
        def __init__(self):
            self._data = []
        def select(self, *args, **kwargs):
            return self
        def count(self, *args, **kwargs):
            return self
        def limit(self, n):
            return self
        async def execute(self):
            return Mock(data=self._data)

    query_builder = AsyncQueryBuilder()
    query_builder._data = []  # Empty data for health check

    mock.table = Mock(return_value=query_builder)

    return mock


@pytest.mark.asyncio
class TestStartupEvent:
    """Test FastAPI startup event."""

    async def test_startup_calls_init_supabase(self):
        """Test that startup event initializes Supabase client."""
        with patch('main.init_supabase') as mock_init_supabase:
            with patch('main.init_db_pool'):
                with patch('main.start_scheduler'):
                    # Import after patching to avoid immediate execution
                    import main

                    # Manually call startup event
                    await main.startup_event()

                    mock_init_supabase.assert_called_once()

    async def test_startup_calls_init_db_pool(self):
        """Test that startup event initializes DB pool."""
        with patch('main.init_supabase'):
            with patch('main.init_db_pool') as mock_init_db_pool:
                with patch('main.start_scheduler'):
                    # Import after patching to avoid immediate execution
                    import main

                    # Manually call startup event
                    await main.startup_event()

                    mock_init_db_pool.assert_called_once()

    async def test_startup_starts_scheduler(self):
        """Test that startup event starts the scheduler."""
        with patch('main.init_supabase'):
            with patch('main.init_db_pool'):
                with patch('main.start_scheduler') as mock_start_scheduler:
                    # Import after patching to avoid immediate execution
                    import main

                    # Manually call startup event
                    await main.startup_event()

                    mock_start_scheduler.assert_called_once()


@pytest.mark.asyncio
class TestHealthEndpoints:
    """Test health check endpoints."""

    def test_health_endpoint_returns_healthy(self):
        """Test that /health returns healthy status."""
        with patch('main.init_supabase'):
            with patch('main.init_db_pool'):
                with patch('main.start_scheduler'):
                    from main import app
                    from fastapi.testclient import TestClient

                    client = TestClient(app)
                    response = client.get("/health")

                    assert response.status_code == 200
                    assert response.json() == {"status": "healthy"}

    def test_read_root_returns_ok(self):
        """Test that root endpoint returns ok status."""
        with patch('main.init_supabase'):
            with patch('main.init_db_pool'):
                with patch('main.start_scheduler'):
                    from main import app
                    from fastapi.testclient import TestClient

                    client = TestClient(app)
                    response = client.get("/")

                    assert response.status_code == 200
                    assert response.json()["status"] == "ok"

    @pytest.mark.asyncio
    async def test_db_health_endpoint_returns_connected(self, mock_supabase_client):
        """Test that /db-health returns connected status when DB is reachable."""
        with patch('main.supabase', mock_supabase_client):
            from main import db_health_check

            result = await db_health_check()

            assert result["status"] == "connected"
            assert "data" in result

    @pytest.mark.asyncio
    async def test_db_health_endpoint_raises_on_error(self):
        """Test that /db-health raises 500 when DB is unreachable."""
        mock_supabase = AsyncMock()
        mock_supabase.table.side_effect = Exception("Connection failed")

        with patch('main.supabase', mock_supabase):
            with patch('main.init_supabase'):
                with patch('main.init_db_pool'):
                    with patch('main.start_scheduler'):
                        from main import db_health_check
                        from fastapi import HTTPException

                        with pytest.raises(HTTPException) as exc_info:
                            await db_health_check()

                        assert exc_info.value.status_code == 500
