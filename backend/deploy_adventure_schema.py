#!/usr/bin/env python3
"""
Deploy Adventure Mode schema to Supabase.

This script deploys all Adventure Mode SQL files in the correct order:
1. schema_monsters.sql - Create monsters table
2. seed_monsters.sql - Populate monsters
3. schema_adventures.sql - Create adventures table
4. migrations/add_adventure_to_profiles.sql - Add adventure stats to profiles
5. migrations/add_adventure_to_daily_entries.sql - Add adventure_id to daily_entries

Usage:
    python deploy_adventure_schema.py
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
    """Verify that all tables and columns were created successfully."""
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

        # Check monsters table
        try:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'monsters'
                );
            """)
            if cursor.fetchone()[0]:
                print("✓ monsters table exists")
            else:
                print("✗ monsters table missing")
                all_ok = False

            # Check monster count
            cursor.execute("SELECT COUNT(*) FROM monsters;")
            count = cursor.fetchone()[0]
            if count == 42:
                print(f"✓ monsters seeded: {count} monsters")
            else:
                print(f"⚠ monsters seeded: {count} monsters (expected 42)")
        except Exception as e:
            print(f"✗ Failed to verify monsters: {e}")
            all_ok = False

        # Check adventures table
        try:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'adventures'
                );
            """)
            if cursor.fetchone()[0]:
                print("✓ adventures table exists")
            else:
                print("✗ adventures table missing")
                all_ok = False
        except Exception as e:
            print(f"✗ Failed to verify adventures: {e}")
            all_ok = False

        # Check daily_entries has adventure_id
        try:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns
                    WHERE table_name = 'daily_entries'
                    AND column_name = 'adventure_id'
                );
            """)
            if cursor.fetchone()[0]:
                print("✓ daily_entries.adventure_id column exists")
            else:
                print("✗ daily_entries.adventure_id column missing")
                all_ok = False
        except Exception as e:
            print(f"✗ Failed to verify daily_entries: {e}")
            all_ok = False

        # Check profiles has adventure columns
        try:
            cursor.execute("""
                SELECT COUNT(*)
                FROM information_schema.columns
                WHERE table_name = 'profiles'
                AND column_name IN (
                    'current_adventure', 'adventure_count', 'adventure_win_count',
                    'monster_defeats', 'monster_escapes', 'monster_rating',
                    'highest_tier_reached'
                );
            """)
            count = cursor.fetchone()[0]
            if count == 7:
                print(f"✓ profiles adventure columns exist ({count}/7)")
            else:
                print(f"⚠ profiles adventure columns: {count}/7 found")
        except Exception as e:
            print(f"✗ Failed to verify profiles: {e}")
            all_ok = False

        cursor.close()
        return_db_connection(conn)

        return all_ok

    except Exception as e:
        print(f"✗ Verification failed: {e}")
        return False


def main():
    """Deploy all Adventure Mode schema files."""
    print("\n" + "="*60)
    print("ADVENTURE MODE SCHEMA DEPLOYMENT")
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

    # Deploy in order (dependencies matter!)
    base_path = os.path.dirname(os.path.abspath(__file__))

    results['monsters'] = deploy_sql_file(
        os.path.join(base_path, 'schema_monsters.sql'),
        'Monsters Table'
    )

    results['seed_monsters'] = deploy_sql_file(
        os.path.join(base_path, 'seed_monsters.sql'),
        'Monster Data Seeding'
    )

    results['adventures'] = deploy_sql_file(
        os.path.join(base_path, 'schema_adventures.sql'),
        'Adventures Table'
    )

    results['profiles'] = deploy_sql_file(
        os.path.join(base_path, 'migrations/add_adventure_to_profiles.sql'),
        'Profiles Adventure Stats'
    )

    results['daily_entries'] = deploy_sql_file(
        os.path.join(base_path, 'migrations/add_adventure_to_daily_entries.sql'),
        'Daily Entries Adventure Support'
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
