#!/usr/bin/env python3
"""
Test script to verify migration 001_add_task_categories_and_monster_types.sql

This script:
1. Connects to the database
2. Runs verification queries for all schema changes
3. Reports results

Usage:
    python tests/scripts/test_migration_001.py
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dotenv import load_dotenv
import asyncpg

load_dotenv()


async def run_tests():
    """Run all migration verification tests."""

    # Get database URL from environment
    database_url = os.environ.get("SUPABASE_URI")
    if not database_url:
        print("❌ SUPABASE_URI not found in environment variables")
        return False

    print(f"🔗 Connecting to database...")

    try:
        conn = await asyncpg.connect(database_url)
        print("✅ Connected to database\n")
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        return False

    all_passed = True

    # =========================================================================
    # Test 1: tasks.category column exists
    # =========================================================================
    print("=" * 60)
    print("Test 1: Verify tasks.category column exists")
    print("=" * 60)

    try:
        result = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns
                WHERE table_name = 'tasks'
                AND column_name = 'category'
            );
        """)
        if result:
            print("✅ PASS: category column exists in tasks table")
        else:
            print("❌ FAIL: category column does NOT exist in tasks table")
            all_passed = False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        all_passed = False

    # =========================================================================
    # Test 2: tasks.category has correct CHECK constraint
    # =========================================================================
    print("\n" + "=" * 60)
    print("Test 2: Verify tasks.category CHECK constraint")
    print("=" * 60)

    try:
        result = await conn.fetchval("""
            SELECT pg_get_constraintdef(oid)
            FROM pg_constraint
            WHERE conrelid = 'tasks'::regclass
            AND conname LIKE '%category%';
        """)
        if result and all(cat in result for cat in ['errand', 'focus', 'physical', 'creative', 'social', 'wellness', 'organization']):
            print("✅ PASS: category constraint has all valid values")
            print(f"   Constraint: {result}")
        else:
            print(f"❌ FAIL: category constraint missing or incomplete")
            print(f"   Got: {result}")
            all_passed = False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        all_passed = False

    # =========================================================================
    # Test 3: monsters.monster_type column exists
    # =========================================================================
    print("\n" + "=" * 60)
    print("Test 3: Verify monsters.monster_type column exists")
    print("=" * 60)

    try:
        result = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns
                WHERE table_name = 'monsters'
                AND column_name = 'monster_type'
            );
        """)
        if result:
            print("✅ PASS: monster_type column exists in monsters table")
        else:
            print("❌ FAIL: monster_type column does NOT exist in monsters table")
            all_passed = False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        all_passed = False

    # =========================================================================
    # Test 4: monsters.monster_type is NOT NULL
    # =========================================================================
    print("\n" + "=" * 60)
    print("Test 4: Verify monsters.monster_type is NOT NULL")
    print("=" * 60)

    try:
        result = await conn.fetchval("""
            SELECT is_nullable
            FROM information_schema.columns
            WHERE table_name = 'monsters'
            AND column_name = 'monster_type';
        """)
        if result == 'NO':
            print("✅ PASS: monster_type is NOT NULL")
        else:
            print(f"❌ FAIL: monster_type is nullable (is_nullable={result})")
            all_passed = False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        all_passed = False

    # =========================================================================
    # Test 5: All monsters have a monster_type
    # =========================================================================
    print("\n" + "=" * 60)
    print("Test 5: Verify all monsters have monster_type assigned")
    print("=" * 60)

    try:
        result = await conn.fetchval("""
            SELECT COUNT(*) FROM monsters WHERE monster_type IS NULL;
        """)
        if result == 0:
            print("✅ PASS: All 42 monsters have monster_type assigned")
        else:
            print(f"❌ FAIL: {result} monsters have NULL monster_type")
            all_passed = False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        all_passed = False

    # =========================================================================
    # Test 6: type_effectiveness table exists
    # =========================================================================
    print("\n" + "=" * 60)
    print("Test 6: Verify type_effectiveness table exists")
    print("=" * 60)

    try:
        result = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'type_effectiveness'
            );
        """)
        if result:
            print("✅ PASS: type_effectiveness table exists")
        else:
            print("❌ FAIL: type_effectiveness table does NOT exist")
            all_passed = False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        all_passed = False

    # =========================================================================
    # Test 7: type_effectiveness has 49 rows
    # =========================================================================
    print("\n" + "=" * 60)
    print("Test 7: Verify type_effectiveness has 49 rows")
    print("=" * 60)

    try:
        result = await conn.fetchval("SELECT COUNT(*) FROM type_effectiveness;")
        if result == 49:
            print(f"✅ PASS: type_effectiveness has {result} rows")
        else:
            print(f"❌ FAIL: type_effectiveness has {result} rows (expected 49)")
            all_passed = False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        all_passed = False

    # =========================================================================
    # Test 8: type_discoveries table exists
    # =========================================================================
    print("\n" + "=" * 60)
    print("Test 8: Verify type_discoveries table exists")
    print("=" * 60)

    try:
        result = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'type_discoveries'
            );
        """)
        if result:
            print("✅ PASS: type_discoveries table exists")
        else:
            print("❌ FAIL: type_discoveries table does NOT exist")
            all_passed = False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        all_passed = False

    # =========================================================================
    # Test 9: type_discoveries has correct columns
    # =========================================================================
    print("\n" + "=" * 60)
    print("Test 9: Verify type_discoveries has correct columns")
    print("=" * 60)

    try:
        result = await conn.fetch("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'type_discoveries'
            ORDER BY ordinal_position;
        """)
        columns = {row['column_name'] for row in result}
        required_columns = {
            'id', 'user_id', 'monster_type', 'task_category',
            'effectiveness', 'discovered_at'
        }
        if required_columns.issubset(columns):
            print("✅ PASS: type_discoveries has all required columns")
            print(f"   Columns: {', '.join(sorted(columns))}")
        else:
            print(f"❌ FAIL: Missing columns: {required_columns - columns}")
            all_passed = False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        all_passed = False

    # =========================================================================
    # Test 10: idx_type_discoveries_user_monster index exists
    # =========================================================================
    print("\n" + "=" * 60)
    print("Test 10: Verify idx_type_discoveries_user_monster index exists")
    print("=" * 60)

    try:
        result = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM pg_indexes
                WHERE tablename = 'type_discoveries'
                AND indexname = 'idx_type_discoveries_user_monster'
            );
        """)
        if result:
            print("✅ PASS: idx_type_discoveries_user_monster index exists")
        else:
            print("❌ FAIL: idx_type_discoveries_user_monster index does NOT exist")
            all_passed = False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        all_passed = False

    # =========================================================================
    # Test 11: RLS policies on type_effectiveness
    # =========================================================================
    print("\n" + "=" * 60)
    print("Test 11: Verify RLS policies on type_effectiveness")
    print("=" * 60)

    try:
        # Check RLS is enabled
        rls_enabled = await conn.fetchval("""
            SELECT relrowsecurity
            FROM pg_class
            WHERE relname = 'type_effectiveness';
        """)

        # Check for public read policy
        policy_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM pg_policies
                WHERE tablename = 'type_effectiveness'
                AND policyname = 'Type effectiveness is viewable by everyone'
            );
        """)

        if rls_enabled and policy_exists:
            print("✅ PASS: RLS enabled with public read policy")
        else:
            print(f"❌ FAIL: RLS enabled={rls_enabled}, policy exists={policy_exists}")
            all_passed = False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        all_passed = False

    # =========================================================================
    # Test 12: RLS policies on type_discoveries
    # =========================================================================
    print("\n" + "=" * 60)
    print("Test 12: Verify RLS policies on type_discoveries")
    print("=" * 60)

    try:
        # Check RLS is enabled
        rls_enabled = await conn.fetchval("""
            SELECT relrowsecurity
            FROM pg_class
            WHERE relname = 'type_discoveries';
        """)

        # Check for policies
        policies = await conn.fetch("""
            SELECT policyname
            FROM pg_policies
            WHERE tablename = 'type_discoveries';
        """)
        policy_names = {row['policyname'] for row in policies}

        expected_policies = {
            'Users can view their own discoveries',
            'Users can insert their own discoveries'
        }

        if rls_enabled and expected_policies.issubset(policy_names):
            print("✅ PASS: RLS enabled with required policies")
            print(f"   Policies: {', '.join(policy_names)}")
        else:
            print(f"❌ FAIL: RLS enabled={rls_enabled}, missing policies: {expected_policies - policy_names}")
            all_passed = False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        all_passed = False

    # =========================================================================
    # Test 13: Monster type distribution
    # =========================================================================
    print("\n" + "=" * 60)
    print("Test 13: Verify monster type distribution")
    print("=" * 60)

    try:
        results = await conn.fetch("""
            SELECT monster_type, tier, COUNT(*) as count
            FROM monsters
            GROUP BY monster_type, tier
            ORDER BY tier, monster_type;
        """)

        print("   Monster type distribution:")
        for row in results:
            print(f"     {row['monster_type']:12} {row['tier']:8} {row['count']}")

        # Verify all 42 monsters have types
        total = await conn.fetchval("SELECT COUNT(*) FROM monsters WHERE monster_type IS NOT NULL;")
        if total == 42:
            print(f"✅ PASS: All {total} monsters have types assigned")
        else:
            print(f"❌ FAIL: Only {total}/42 monsters have types")
            all_passed = False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        all_passed = False

    # =========================================================================
    # Test 14: Type effectiveness matrix values
    # =========================================================================
    print("\n" + "=" * 60)
    print("Test 14: Verify type effectiveness matrix")
    print("=" * 60)

    try:
        results = await conn.fetch("""
            SELECT monster_type, task_category, multiplier
            FROM type_effectiveness
            ORDER BY monster_type, task_category;
        """)

        # Check that all multipliers are valid
        multipliers = {row['multiplier'] for row in results}
        valid_multipliers = {0.5, 1.0, 1.5}

        if multipliers == valid_multipliers:
            print(f"✅ PASS: All multipliers are valid ({sorted(multipliers)})")
        else:
            print(f"❌ FAIL: Invalid multipliers found: {multipliers - valid_multipliers}")
            all_passed = False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        all_passed = False

    # =========================================================================
    # Summary
    # =========================================================================
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    if all_passed:
        print("✅ ALL TESTS PASSED!")
        print("\nMigration 001_add_task_categories_and_monster_types.sql")
        print("has been successfully applied.")
    else:
        print("❌ SOME TESTS FAILED!")
        print("\nPlease review the failures above and apply the migration.")
        print("\nTo apply the migration, run:")
        print("  1. Open Supabase SQL Editor")
        print("  2. Paste contents of: backend/migrations/001_add_task_categories_and_monster_types.sql")
        print("  3. Execute the script")

    await conn.close()
    return all_passed


if __name__ == "__main__":
    success = asyncio.run(run_tests())
    sys.exit(0 if success else 1)
