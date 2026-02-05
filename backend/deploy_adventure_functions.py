#!/usr/bin/env python3
"""
Deploy Adventure Mode functions to Supabase.

This script deploys:
1. Break feature for battles table (migrations/add_break_to_battles.sql)
2. Adventure round processing function (functions_adventure.sql)

Usage:
    python deploy_adventure_functions.py
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def deploy_sql_file(filepath, description):
    """Deploy a single SQL file to the database."""
    print(f"\n{'='*60}")
    print(f"Deploying: {description}")
    print(f"File: {filepath}")
    print('='*60)

    # Check file exists
    if not os.path.exists(filepath):
        print(f"✗ File not found: {filepath}")
        return False

    # Read the SQL file
    try:
        with open(filepath, 'r') as f:
            sql_content = f.read()
        print(f"✓ Read {len(sql_content)} characters from {filepath}")
    except Exception as e:
        print(f"✗ Failed to read {filepath}: {e}")
        return False

    # Get database connection
    try:
        from database import get_db_connection, return_db_connection
        conn = get_db_connection()

        if not conn:
            print("✗ No database connection available. Check SUPABASE_URI environment variable.")
            return False

        print("✓ Database connection established")

        # Execute SQL
        cursor = conn.cursor()
        try:
            cursor.execute(sql_content)
            conn.commit()
            print(f"✓ SQL executed successfully")
            return True

        except Exception as e:
            conn.rollback()
            print(f"✗ SQL execution failed: {e}")
            return False
        finally:
            cursor.close()
            return_db_connection(conn)

    except ImportError as e:
        print(f"✗ Failed to import database module: {e}")
        return False
    except Exception as e:
        print(f"✗ Deployment failed: {e}")
        return False


def verify_deployment():
    """Verify that all changes were deployed successfully."""
    print(f"\n{'='*60}")
    print("VERIFYING DEPLOYMENT")
    print('='*60)

    try:
        from database import get_db_connection, return_db_connection
        conn = get_db_connection()

        if not conn:
            print("✗ No database connection available")
            return False

        cursor = conn.cursor()
        all_ok = True

        # Check battles break columns
        try:
            cursor.execute("""
                SELECT COUNT(*)
                FROM information_schema.columns
                WHERE table_name = 'battles'
                AND column_name IN (
                    'break_days_used', 'max_break_days', 'is_on_break',
                    'break_end_date', 'break_requested_by', 'break_request_expires_at'
                );
            """)
            count = cursor.fetchone()[0]
            if count == 6:
                print(f"✓ battles table has all 6 break columns ({count}/6)")
            else:
                print(f"⚠ battles break columns: {count}/6 found")
                all_ok = False
        except Exception as e:
            print(f"✗ Failed to verify battles: {e}")
            all_ok = False

        # Check calculate_adventure_round function
        try:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM pg_proc
                    WHERE proname = 'calculate_adventure_round'
                );
            """)
            exists = cursor.fetchone()[0]
            if exists:
                print(f"✓ calculate_adventure_round function exists")
            else:
                print(f"✗ calculate_adventure_round function not found")
                all_ok = False
        except Exception as e:
            print(f"✗ Failed to verify function: {e}")
            all_ok = False

        cursor.close()
        return_db_connection(conn)

        return all_ok

    except Exception as e:
        print(f"✗ Verification failed: {e}")
        return False


def main():
    """Deploy all Adventure Mode functions."""
    print("\n" + "="*60)
    print("ADVENTURE MODE FUNCTIONS DEPLOYMENT")
    print("="*60)

    # Check environment
    database_url = os.environ.get("SUPABASE_URI")
    if not database_url:
        print("✗ SUPABASE_URI environment variable not set")
        print("  Please set it in your .env file")
        return 1

    print(f"✓ Environment configured")

    # Track results
    results = {}

    # Deploy in order
    base_path = os.path.dirname(os.path.abspath(__file__))

    results['battles_break'] = deploy_sql_file(
        os.path.join(base_path, 'migrations/add_break_to_battles.sql'),
        'Battles Break Feature'
    )

    results['adventure_functions'] = deploy_sql_file(
        os.path.join(base_path, 'functions_adventure.sql'),
        'Adventure Round Processing Function'
    )

    # Summary
    print("\n" + "="*60)
    print("DEPLOYMENT SUMMARY")
    print("="*60)
    for name, success in results.items():
        status = "✓ SUCCESS" if success else "✗ FAILED"
        print(f"{name}: {status}")

    # Verify deployment
    if all(results.values()):
        print("\n✓ All SQL files deployed successfully!")
        if verify_deployment():
            print("\n✓ Deployment verification passed!")
            return 0
        else:
            print("\n⚠ Deployment completed but verification found issues.")
            return 1
    else:
        print("\n✗ Some deployments failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
