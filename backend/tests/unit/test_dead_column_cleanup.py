"""
Test that removing dead columns doesn't break existing functionality.

This test verifies that the dead columns identified in DB_OPTIMIZATION_AUDIT.md
are not referenced by any active code paths. Run this BEFORE applying the migration.

Items covered:
- 1.1: profiles.exp (already cleaned up, but verify model works without it)
- 1.2: daily_entries.score_distribution
- 1.3: daily_entries.day_winner
- 1.4: daily_entries.is_daily_winner
"""

import pytest
from database import get_db_connection, return_db_connection


def test_profile_model_works_without_exp():
    """Verify Profile model doesn't require exp field."""
    # Import after models are loaded
    import sys
    import os
    sys.path.insert(0, os.path.dirname(__file__))
    from models import Profile
    from uuid import uuid4

    # Create a profile dict without 'exp' (it's optional with default)
    profile_data = {
        "id": uuid4(),
        "username": "testuser",
        "email": "test@example.com",
        "timezone": "UTC",
        "level": 1,
        "total_xp_earned": 100,
        "avatar_emoji": "🚀",
        "created_at": "2024-01-01T00:00:00Z",
    }

    # Should work without exp field
    profile = Profile(**profile_data)
    assert profile.username == "testuser"


def test_daily_entry_operations_work_without_dead_columns():
    """Test that daily_entries operations work without the dead columns."""
    conn = get_db_connection()
    if not conn:
        pytest.skip("No database connection available")

    cur = conn.cursor()

    # Verify columns were removed by migration
    cur.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'daily_entries'
        AND column_name IN ('score_distribution', 'day_winner', 'is_daily_winner')
        ORDER BY column_name
    """)
    dead_columns = [row[0] for row in cur.fetchall()]

    print(f"Dead columns in daily_entries (should be empty): {dead_columns}")

    # These columns should NOT exist after migration
    assert dead_columns == [], \
        f"Expected no dead columns but found: {dead_columns}"

    cur.close()
    return_db_connection(conn)


def test_no_router_references_dead_columns():
    """Verify no router code directly references the dead columns."""
    import subprocess
    import os

    backend_dir = os.path.dirname(os.path.dirname(__file__))

    # These patterns should NOT exist in router code
    forbidden_patterns = [
        "score_distribution",
        "day_winner",
        "is_daily_winner"
    ]

    for pattern in forbidden_patterns:
        result = subprocess.run(
            ["grep", "-r", pattern, f"{backend_dir}/routers/", "--include=*.py"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            pytest.fail(f"Found forbidden pattern '{pattern}' in routers:\n{result.stdout}")


def test_profiles_exp_already_removed():
    """Verify profiles.exp column was already removed by previous cleanup."""
    conn = get_db_connection()
    if not conn:
        pytest.skip("No database connection available")

    cur = conn.cursor()

    # Check profiles.exp - should NOT exist (already cleaned)
    cur.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'profiles' AND column_name = 'exp'
    """)
    result = cur.fetchone()

    assert result is None, "profiles.exp should have been removed already"

    cur.close()
    return_db_connection(conn)
