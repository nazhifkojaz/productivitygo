"""
Unit tests for async database module.

Tests async client initialization, DB pool, and retry decorators.
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
import asyncio
import importlib


@pytest.mark.asyncio
class TestInitSupabase:
    """Test async Supabase client initialization."""

    async def test_init_supabase_creates_async_client(self):
        """Test that init_supabase creates an AsyncClient."""
        from database import init_supabase, supabase
        import database

        original_client = supabase._client
        try:
            with patch('database.create_async_client') as mock_create:
                mock_client = AsyncMock()
                mock_create.return_value = mock_client

                await init_supabase()

                # Verify client was created
                mock_create.assert_called_once()

                # Verify the proxy's _client was set
                assert supabase._client is mock_client
        finally:
            # Restore the proxy's _client to prevent leaking AsyncMock
            # into other tests. init_supabase() sets supabase._client on
            # the _SupabaseProxy instance shared by all modules.
            supabase._client = original_client


@pytest.mark.asyncio
class TestInitDbPool:
    """Test async DB pool initialization."""

    async def test_init_db_pool_creates_asyncpg_pool(self):
        """Test that init_db_pool creates an asyncpg pool."""
        from database import init_db_pool
        import database

        mock_pool = AsyncMock()

        # Create a mock asyncpg module with create_pool function
        mock_asyncpg = Mock()
        mock_asyncpg.create_pool = AsyncMock(return_value=mock_pool)

        # Patch the import of asyncpg inside init_db_pool
        with patch('builtins.__import__', side_effect=lambda name, *args, **kwargs: mock_asyncpg if name == 'asyncpg' else __import__(name, *args, **kwargs)):
            database.db_pool = None  # Reset before test
            await init_db_pool()

            # Verify the module-level db_pool was set
            assert database.db_pool is not None

    async def test_init_db_pool_handles_import_error(self):
        """Test that init_db_pool handles asyncpg not installed."""
        from database import init_db_pool
        import database

        # Patch the import inside init_db_pool function
        with patch('builtins.__import__', side_effect=lambda name, *args, **kwargs: (_ for _ in ()).throw(ImportError("asyncpg not installed")) if name == 'asyncpg' else __import__(name, *args, **kwargs)):
            # Set db_pool to None before test
            database.db_pool = None

            # Should not raise exception
            await init_db_pool()

            # Pool should remain None
            assert database.db_pool is None


@pytest.mark.asyncio
class TestGetDbConnection:
    """Test async DB connection helpers."""

    async def test_get_db_connection_returns_connection(self):
        """Test that get_db_connection returns a connection from pool."""
        mock_pool = AsyncMock()
        mock_conn = AsyncMock()
        mock_pool.acquire = AsyncMock(return_value=mock_conn)

        from database import get_db_connection

        # Patch db_pool
        import database
        database.db_pool = mock_pool

        conn = await get_db_connection()

        mock_pool.acquire.assert_called_once()
        assert conn == mock_conn

    async def test_get_db_connection_returns_none_when_no_pool(self):
        """Test that get_db_connection returns None when pool not initialized."""
        from database import get_db_connection

        # Patch db_pool to None
        import database
        database.db_pool = None

        conn = await get_db_connection()

        assert conn is None

    async def test_return_db_connection_releases_to_pool(self):
        """Test that return_db_connection releases connection back to pool."""
        mock_pool = AsyncMock()
        mock_conn = AsyncMock()
        mock_pool.release = AsyncMock()

        from database import return_db_connection

        # Patch db_pool
        import database
        database.db_pool = mock_pool

        await return_db_connection(mock_conn)

        mock_pool.release.assert_called_once_with(mock_conn)


@pytest.mark.asyncio
class TestAsyncRetryDecorator:
    """Test async retry on connection error decorator."""

    async def test_succeeds_on_first_attempt(self):
        """Test that decorated function succeeds on first try."""
        from database import async_retry_on_connection_error

        mock_func = AsyncMock(return_value="success")

        decorated = async_retry_on_connection_error()(mock_func)
        result = await decorated()

        assert result == "success"
        mock_func.assert_called_once()

    async def test_retries_on_connection_error(self):
        """Test that decorated function retries on connection errors."""
        from database import async_retry_on_connection_error

        mock_func = AsyncMock(side_effect=[Exception("network error"), "success"])

        decorated = async_retry_on_connection_error(max_retries=3, delay=0.01)(mock_func)
        result = await decorated()

        assert result == "success"
        assert mock_func.call_count == 2

    async def test_fails_after_max_retries(self):
        """Test that decorated function raises after max retries exhausted."""
        from database import async_retry_on_connection_error

        mock_func = AsyncMock(side_effect=Exception("network error"))

        decorated = async_retry_on_connection_error(max_retries=2, delay=0.01)(mock_func)

        with pytest.raises(Exception) as exc_info:
            await decorated()

        assert "network error" in str(exc_info.value)
        assert mock_func.call_count == 2

    async def test_raises_immediately_on_non_connection_error(self):
        """Test that non-connection errors raise immediately without retry."""
        from database import async_retry_on_connection_error

        mock_func = AsyncMock(side_effect=ValueError("invalid input"))

        decorated = async_retry_on_connection_error(max_retries=3, delay=0.01)(mock_func)

        with pytest.raises(ValueError, match="invalid input"):
            await decorated()

        # Should not retry
        mock_func.assert_called_once()


@pytest.mark.asyncio
class TestSyncRetryDecorator:
    """Test sync retry decorator (legacy, kept for backward compatibility)."""

    def test_sync_decorator_succeeds_on_first_attempt(self):
        """Test that sync decorated function succeeds on first try."""
        from database import retry_on_connection_error

        mock_func = Mock(return_value="success")

        decorated = retry_on_connection_error()(mock_func)
        result = decorated()

        assert result == "success"
        mock_func.assert_called_once()

    def test_sync_decorator_retries_on_connection_error(self):
        """Test that sync decorated function retries on connection errors."""
        import time
        from database import retry_on_connection_error

        mock_func = Mock(side_effect=[Exception("network error"), "success"])

        decorated = retry_on_connection_error(max_retries=3, delay=0.01)(mock_func)
        result = decorated()

        assert result == "success"
        assert mock_func.call_count == 2
