import os
from dotenv import load_dotenv
from supabase import create_async_client, AsyncClient
import asyncio
from functools import wraps

load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_SERVICE_KEY")
database_url: str = os.environ.get("SUPABASE_URI")  # PostgreSQL connection string

if not url or not key:
    raise ValueError("Missing SUPABASE_URL or SUPABASE_SERVICE_KEY environment variables")


class _SupabaseProxy:
    """
    Proxy that forwards attribute access to the real async Supabase client.

    Solves the import-time binding problem: other modules do
    ``from database import supabase`` which captures a reference to THIS
    object.  When ``init_supabase()`` later sets ``_client``, every module
    sees the real client through the same proxy — no stale ``None`` refs.
    """
    _client: AsyncClient = None

    def __getattr__(self, name):
        if self._client is None:
            raise AttributeError(
                f"Supabase client not initialized (accessing '{name}'). "
                "Ensure init_supabase() is called at startup."
            )
        return getattr(self._client, name)


# All modules import this proxy; init_supabase() fills in _client later.
supabase: AsyncClient = _SupabaseProxy()

# Async PostgreSQL connection pool (more stable than REST API)
db_pool = None


async def init_supabase():
    """
    Initialize the async Supabase client.

    Must be called at application startup (e.g., in FastAPI startup event).
    Cannot be called at module import time because create_async_client is a coroutine.
    """
    supabase._client = await create_async_client(url, key)
    print("✓ Async Supabase client initialized")


async def init_db_pool():
    """
    Initialize the async PostgreSQL connection pool.

    Used for integration tests that need direct DB access.
    """
    global db_pool
    if database_url:
        try:
            import asyncpg
            db_pool = await asyncpg.create_pool(
                database_url,
                min_size=1,
                max_size=10
            )
            print("✓ Async PostgreSQL connection pool initialized")
        except ImportError:
            print("⚠ asyncpg not installed. Install with: pip install asyncpg")
        except Exception as e:
            print(f"⚠ Failed to create DB pool: {e}")


async def get_db_connection():
    """Get a connection from the async pool"""
    if db_pool:
        return await db_pool.acquire()
    return None


async def return_db_connection(conn):
    """Return a connection to the async pool"""
    if db_pool and conn:
        await db_pool.release(conn)


def async_retry_on_connection_error(max_retries=3, delay=0.5):
    """
    Async decorator to retry Supabase operations on connection errors.

    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries (exponential backoff)
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    error_msg = str(e).lower()

                    # Only retry on connection-related errors
                    if any(keyword in error_msg for keyword in ['disconnect', 'connection', 'timeout', 'network']):
                        if attempt < max_retries - 1:
                            wait_time = delay * (2 ** attempt)  # Exponential backoff
                            print(f"Connection error on attempt {attempt + 1}/{max_retries}, retrying in {wait_time}s: {e}")
                            await asyncio.sleep(wait_time)
                            continue
                    # For non-connection errors, raise immediately
                    raise

            # All retries exhausted
            raise last_exception
        return wrapper
    return decorator


# Legacy sync decorator (kept for backward compatibility during migration)
# TODO: Remove after all callers are migrated to async
def retry_on_connection_error(max_retries=3, delay=0.5):
    """
    Decorator to retry Supabase operations on connection errors (sync version).

    DEPRECATED: Use async_retry_on_connection_error for async functions.
    """
    import time
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    error_msg = str(e).lower()

                    # Only retry on connection-related errors
                    if any(keyword in error_msg for keyword in ['disconnect', 'connection', 'timeout', 'network']):
                        if attempt < max_retries - 1:
                            wait_time = delay * (2 ** attempt)  # Exponential backoff
                            print(f"Connection error on attempt {attempt + 1}/{max_retries}, retrying in {wait_time}s: {e}")
                            time.sleep(wait_time)
                            continue
                    # For non-connection errors, raise immediately
                    raise

            # All retries exhausted
            raise last_exception
        return wrapper
    return decorator
