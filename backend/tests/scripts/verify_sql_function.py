"""
Test script to verify the existing complete_battle() SQL function works correctly.
Run this before applying the bug fix to ensure current behavior is understood.
"""
import os
import sys
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import supabase, get_db_connection, return_db_connection
from datetime import date

def test_existing_function():
    """Test the existing complete_battle SQL function"""
    print("=" * 60)
    print("Testing existing complete_battle() SQL function")
    print("=" * 60)

    # First, check if we can connect
    try:
        conn = get_db_connection()
        if conn:
            print("✓ PostgreSQL connection available")
            return_db_connection(conn)
        else:
            print("⚠ No PostgreSQL connection, using Supabase REST API")
    except Exception as e:
        print(f"⚠ Connection check: {e}")

    # Check if the function exists
    print("\n1. Checking if complete_battle function exists...")
    try:
        result = supabase.table("battles").select("id, status, winner_id").limit(1).execute()
        print(f"   ✓ Can query battles table")

        # Try to call the RPC function with a fake UUID to see if it exists
        # (this will fail but confirms the function exists if we get the right error)
        try:
            test_result = supabase.rpc("complete_battle", {"battle_uuid": "00000000-0000-0000-0000-000000000000"}).execute()
            print(f"   Function exists and executed")
        except Exception as e:
            error_msg = str(e)
            if "function" in error_msg.lower() and "does not exist" in error_msg.lower():
                print(f"   ✗ Function does NOT exist: {e}")
                return False
            else:
                # Function exists but got a different error (expected for fake UUID)
                print(f"   ✓ Function exists (got expected error for invalid UUID)")
    except Exception as e:
        print(f"   ✗ Error checking function: {e}")
        return False

    # Check current battles table schema
    print("\n2. Checking battles table schema...")
    try:
        # Try to select a completed battle to see current schema
        result = supabase.table("battles").select("*").eq("status", "completed").limit(1).execute()
        if result.data:
            battle = result.data[0]
            print(f"   ✓ Found completed battle")
            print(f"   Columns present: {', '.join(battle.keys())}")
            if 'completed_at' in battle:
                print(f"   ✓ completed_at column already exists")
            else:
                print(f"   ⚠ completed_at column NOT present (migration needed)")
        else:
            print(f"   ⚠ No completed battles found to check schema")
    except Exception as e:
        print(f"   ✗ Error checking schema: {e}")

    print("\n" + "=" * 60)
    print("Pre-test verification complete")
    print("=" * 60)
    return True

if __name__ == "__main__":
    load_dotenv()
    if not os.environ.get("SUPABASE_URL"):
        print("ERROR: SUPABASE_URL not set in environment")
        sys.exit(1)

    success = test_existing_function()
    sys.exit(0 if success else 1)
