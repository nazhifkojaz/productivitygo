"""
Apply BUG-001 fix: Race condition in battle completion.

This script:
1. Applies the database migration (adds completed_at column)
2. Updates the complete_battle() SQL function with idempotency

Run this after reviewing the changes.
"""
import os
import sys
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import supabase, get_db_connection, return_db_connection


def apply_migration():
    """Apply the database migration to add completed_at column."""
    print("=" * 60)
    print("Step 1: Applying database migration")
    print("=" * 60)

    migration_sql = """
    ALTER TABLE battles
    ADD COLUMN IF NOT EXISTS completed_at TIMESTAMPTZ;

    CREATE INDEX IF NOT EXISTS idx_battles_completed_at ON battles(completed_at);

    COMMENT ON COLUMN battles.completed_at IS 'Timestamp when battle was completed. Used for idempotency check to prevent duplicate stat increments from concurrent completion calls.';
    """

    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            for statement in migration_sql.split(';'):
                statement = statement.strip()
                if statement:
                    print(f"  Executing: {statement[:60]}...")
                    cursor.execute(statement)
            conn.commit()
            print("  ✓ Migration applied successfully via PostgreSQL")
            cursor.close()
            return_db_connection(conn)
            return True
        except Exception as e:
            print(f"  ✗ Error applying migration: {e}")
            cursor.close()
            return_db_connection(conn)
            return False

    print("  ⚠ Direct PostgreSQL connection not available")
    print("  Please run the SQL in 'migrations/add_completed_at.sql' manually")
    return False


def apply_sql_function():
    """Apply the updated complete_battle() function."""
    print("\n" + "=" * 60)
    print("Step 2: Updating complete_battle() SQL function")
    print("=" * 60)

    # Read the updated function from file
    function_path = os.path.join(os.path.dirname(__file__), 'functions_battle_scoring.sql')

    try:
        with open(function_path, 'r') as f:
            content = f.read()
    except Exception as e:
        print(f"  ✗ Error reading function file: {e}")
        return False

    # Extract the complete_battle function
    start_marker = "CREATE OR REPLACE FUNCTION complete_battle"
    end_marker = "$$;"

    start_idx = content.find(start_marker)
    if start_idx == -1:
        print("  ✗ Could not find complete_battle function in file")
        return False

    end_idx = content.find(end_marker, start_idx + len(start_marker))
    if end_idx == -1:
        print("  ✗ Could not find function end marker")
        return False

    function_sql = content[start_idx:end_idx + len(end_marker)]

    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            # Need to drop the function first since we're changing the return type
            print(f"  Dropping existing function...")
            cursor.execute("DROP FUNCTION IF EXISTS complete_battle(UUID);")
            print(f"  Executing: CREATE OR REPLACE FUNCTION complete_battle...")
            cursor.execute(function_sql)
            conn.commit()
            print("  ✓ Function updated successfully via PostgreSQL")
            cursor.close()
            return_db_connection(conn)
            return True
        except Exception as e:
            print(f"  ✗ Error applying function: {e}")
            cursor.close()
            return_db_connection(conn)
            return False

    print("  ⚠ Direct PostgreSQL connection not available")
    print("  Please run the SQL in 'functions_battle_scoring.sql' manually")
    return False


def verify_fix():
    """Verify the fix was applied correctly."""
    print("\n" + "=" * 60)
    print("Step 3: Verifying fix")
    print("=" * 60)

    # Check if completed_at column exists
    try:
        result = supabase.table("battles").select("id, completed_at").limit(1).execute()
        if result.data and len(result.data) > 0:
            if 'completed_at' in result.data[0]:
                print("  ✓ completed_at column exists")
            else:
                print("  ✗ completed_at column NOT found")
                return False
    except Exception as e:
        print(f"  ⚠ Could not verify column: {e}")

    # Test the function with a fake UUID (should handle gracefully)
    try:
        result = supabase.rpc("complete_battle", {"battle_uuid": "00000000-0000-0000-0000-000000000000"}).execute()
        print("  ✓ complete_battle() function exists and executed")
    except Exception as e:
        error_msg = str(e)
        if "does not exist" in error_msg:
            print("  ✗ complete_battle() function NOT found")
            return False
        else:
            print("  ✓ complete_battle() function exists (got expected error for fake UUID)")

    print("\n" + "=" * 60)
    print("BUG-001 fix applied successfully!")
    print("=" * 60)
    return True


if __name__ == "__main__":
    load_dotenv()

    if not os.environ.get("SUPABASE_URL"):
        print("ERROR: SUPABASE_URL not set in environment")
        sys.exit(1)

    print("\nBUG-001: Race Condition in Battle Completion")
    print("Applying fix...\n")

    migration_ok = apply_migration()
    function_ok = apply_sql_function()

    if not migration_ok or not function_ok:
        print("\n" + "=" * 60)
        print("MANUAL STEPS REQUIRED")
        print("=" * 60)
        print("Please apply the following manually in Supabase SQL editor:")
        print("1. The SQL from 'migrations/add_completed_at.sql'")
        print("2. The SQL from 'functions_battle_scoring.sql'")
        print("=" * 60)
        sys.exit(1)

    if verify_fix():
        sys.exit(0)
    else:
        sys.exit(1)
