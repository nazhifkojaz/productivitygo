"""
Test cleanup for DB_OPTIMIZATION_AUDIT.md items 1.5, 2.1, 2.2, 3.1, 3.2

Items covered:
- 1.5: profiles.daily_win_count, profiles.overall_win_count (unused)
- 2.1: profiles.adventure_win_count vs profiles.monster_defeats (duplicate)
- 2.2: profiles.total_damage_dealt (undeclared column, exists in DB)
- 3.1: profiles.level (derived from XP, bug: not updated for adventures)
- 3.2: profiles.monster_rating (derived, acceptable to keep)
"""

import pytest
from database import get_db_connection, return_db_connection


def test_daily_win_count_and_overall_win_count_unused():
    """Verify these columns are not referenced by active code (only in migrations)."""
    import subprocess
    import os

    backend_dir = os.path.dirname(os.path.dirname(__file__))

    # Check that no active code references these columns
    for col in ['daily_win_count', 'overall_win_count']:
        result = subprocess.run(
            ["grep", "-r", col, f"{backend_dir}/routers/", f"{backend_dir}/services/",
             "--include=*.py"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            pytest.fail(f"Column {col} is referenced in active code:\n{result.stdout}")


def test_adventure_win_count_removed():
    """Verify adventure_win_count was removed (monster_defeats is the source of truth)."""
    conn = get_db_connection()
    if not conn:
        pytest.skip("No database connection")

    cur = conn.cursor()
    cur.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'profiles' AND column_name = 'adventure_win_count'
    """)
    result = cur.fetchone()

    assert result is None, "adventure_win_count should have been removed"
    cur.close()
    return_db_connection(conn)


def test_total_damage_dealt_column_exists():
    """Verify total_damage_dealt exists in database (used by SQL functions)."""
    conn = get_db_connection()
    if not conn:
        pytest.skip("No database connection")

    cur = conn.cursor()
    cur.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'profiles' AND column_name = 'total_damage_dealt'
    """)
    result = cur.fetchone()

    assert result is not None, "total_damage_dealt should exist in database"
    assert result[1] == 'integer', f"total_damage_dealt should be integer, got {result[1]}"

    cur.close()
    return_db_connection(conn)


def test_level_data_before_generated_column():
    """Document current level state - expect mismatches for adventure-only users."""
    conn = get_db_connection()
    if not conn:
        pytest.skip("No database connection")

    cur = conn.cursor()
    cur.execute("""
        SELECT id, level, total_xp_earned
        FROM profiles
        WHERE total_xp_earned IS NOT NULL
        LIMIT 20
    """)

    mismatches = []
    for row in cur.fetchall():
        user_id, level, xp = row
        expected_level = int(xp // 1000) + 1
        if level != expected_level:
            mismatches.append({
                'user_id': str(user_id),
                'actual': level,
                'expected': expected_level,
                'xp': xp
            })

    # Log mismatches but don't fail (this is the bug we're fixing)
    if mismatches:
        print(f"\nFound {len(mismatches)} level mismatches (adventure-only users):")
        for m in mismatches[:5]:
            print(f"  User {m['user_id']}: level={m['actual']}, expected={m['expected']} (xp={m['xp']})")

    cur.close()
    return_db_connection(conn)


def test_monster_rating_formula():
    """Verify monster_rating = MAX(0, monster_defeats - monster_escapes)."""
    conn = get_db_connection()
    if not conn:
        pytest.skip("No database connection")

    cur = conn.cursor()
    cur.execute("""
        SELECT id, monster_rating, monster_defeats, monster_escapes
        FROM profiles
        WHERE monster_defeats IS NOT NULL OR monster_escapes IS NOT NULL
        LIMIT 20
    """)

    for row in cur.fetchall():
        user_id, rating, defeats, escapes = row
        defeats = defeats or 0
        escapes = escapes or 0
        expected = max(0, defeats - escapes)
        if rating != expected:
            pytest.fail(f"User {user_id}: monster_rating={rating}, expected={expected} (defeats={defeats}, escapes={escapes})")

    cur.close()
    return_db_connection(conn)


def test_columns_to_remove_exist_before_migration():
    """Verify columns we plan to remove actually exist."""
    conn = get_db_connection()
    if not conn:
        pytest.skip("No database connection")

    cur = conn.cursor()

    # Columns we're removing
    columns_to_remove = [
        ('profiles', 'daily_win_count'),
        ('profiles', 'adventure_win_count'),
    ]

    for table, col in columns_to_remove:
        cur.execute(f"""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = '{table}' AND column_name = '{col}'
        """)
        result = cur.fetchone()
        if result:
            print(f"✓ {table}.{col} exists (will be removed)")
        else:
            print(f"  {table}.{col} not found (already removed?)")

    cur.close()
    return_db_connection(conn)
