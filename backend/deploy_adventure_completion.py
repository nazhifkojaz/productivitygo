#!/usr/bin/env python3
"""
Deploy Adventure Mode completion functions to Supabase.

This script deploys:
1. Helper functions (functions_adventure_helpers.sql)
2. Completion functions (functions_adventure_completion.sql)

Usage:
    python deploy_adventure_completion.py
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
    """Verify that all functions were deployed successfully."""
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

        # Check functions exist
        functions = [
            'complete_adventure',
            'abandon_adventure',
            'get_unlocked_tiers'
        ]

        for func_name in functions:
            try:
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM pg_proc
                        WHERE proname = %s
                    );
                """, (func_name,))
                exists = cursor.fetchone()[0]
                if exists:
                    print(f"✓ {func_name} function exists")
                else:
                    print(f"✗ {func_name} function not found")
                    all_ok = False
            except Exception as e:
                print(f"✗ Failed to verify {func_name}: {e}")
                all_ok = False

        # Test get_unlocked_tiers function
        try:
            cursor.execute("SELECT get_unlocked_tiers(0);")
            result = cursor.fetchone()[0]
            expected = ['easy']
            if result == expected:
                print(f"✓ get_unlocked_tiers(0) returns {expected}")
            else:
                print(f"⚠ get_unlocked_tiers(0) returned {result}, expected {expected}")
        except Exception as e:
            print(f"✗ Failed to test get_unlocked_tiers: {e}")
            all_ok = False

        cursor.close()
        return_db_connection(conn)

        return all_ok

    except Exception as e:
        print(f"✗ Verification failed: {e}")
        return False


def main():
    """Deploy all Adventure Mode completion functions."""
    print("\n" + "="*60)
    print("ADVENTURE MODE COMPLETION FUNCTIONS DEPLOYMENT")
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

    results['helpers'] = deploy_sql_file(
        os.path.join(base_path, 'functions_adventure_helpers.sql'),
        'Adventure Helper Functions (get_unlocked_tiers)'
    )

    results['completion'] = deploy_sql_file(
        os.path.join(base_path, 'functions_adventure_completion.sql'),
        'Adventure Completion Functions (complete/abandon)'
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
