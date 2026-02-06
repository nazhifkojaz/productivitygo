"""
Test cleanup for DB_OPTIMIZATION_AUDIT.md item 1.6
Phantom index idx_battles_date on non-existent column battle_date
"""

import pytest
from database import get_db_connection, return_db_connection


def test_battle_date_column_does_not_exist():
    """Verify battle_date column doesn't exist (as per audit)."""
    conn = get_db_connection()
    if not conn:
        pytest.skip("No database connection")

    cur = conn.cursor()
    cur.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'battles' AND column_name = 'battle_date'
    """)
    result = cur.fetchone()

    assert result is None, "battle_date should not exist"
    cur.close()
    return_db_connection(conn)


def test_idx_battles_date_index_does_not_exist():
    """Verify the phantom index was never created."""
    conn = get_db_connection()
    if not conn:
        pytest.skip("No database connection")

    cur = conn.cursor()
    cur.execute("""
        SELECT indexname
        FROM pg_indexes
        WHERE tablename = 'battles' AND indexname = 'idx_battles_date'
    """)
    result = cur.fetchone()

    assert result is None, "idx_battles_date should not exist (phantom index)"
    cur.close()
    return_db_connection(conn)


def test_battles_has_start_and_end_date():
    """Verify battles has start_date and end_date columns."""
    conn = get_db_connection()
    if not conn:
        pytest.skip("No database connection")

    cur = conn.cursor()
    cur.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'battles' AND column_name IN ('start_date', 'end_date')
        ORDER BY column_name
    """)
    results = [row[0] for row in cur.fetchall()]

    assert 'start_date' in results, "start_date should exist"
    assert 'end_date' in results, "end_date should exist"
    cur.close()
    return_db_connection(conn)


def test_start_date_index_exists():
    """Verify idx_battles_start_date index exists."""
    conn = get_db_connection()
    if not conn:
        pytest.skip("No database connection")

    cur = conn.cursor()
    cur.execute("""
        SELECT indexname
        FROM pg_indexes
        WHERE tablename = 'battles' AND indexname = 'idx_battles_start_date'
    """)
    result = cur.fetchone()

    assert result is not None, "idx_battles_start_date should exist"
    cur.close()
    return_db_connection(conn)


def test_all_battles_indexes_are_valid():
    """Verify all indexes on battles reference existing columns."""
    conn = get_db_connection()
    if not conn:
        pytest.skip("No database connection")

    cur = conn.cursor()

    # Get all indexes on battles
    cur.execute("""
        SELECT indexname, indexdef
        FROM pg_indexes
        WHERE tablename = 'battles'
    """)

    invalid_indexes = []
    for idx_name, idx_def in cur.fetchall():
        # Extract column names from index definition
        # This is a simple check - more sophisticated parsing might be needed
        if 'battle_date' in idx_def.lower():
            invalid_indexes.append((idx_name, idx_def))

    if invalid_indexes:
        pytest.fail(f"Found indexes referencing non-existent columns: {invalid_indexes}")

    cur.close()
    return_db_connection(conn)
