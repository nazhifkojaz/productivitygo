"""
Integration tests for Task Categories & Monster Types schema.

These tests verify that:
1. tasks.category column exists with correct constraints
2. monsters.monster_type column exists with correct constraints
3. type_effectiveness table exists with correct data
4. type_discoveries table exists with correct constraints
5. RLS policies are correctly configured
6. All 42 monsters have correct type assignments

Run after deploying migration 001_add_task_categories_and_monster_types.sql.

Usage:
    pytest tests/integration/test_task_categories_schema.py -v
"""
import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    from database import get_db_connection, return_db_connection
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False


# Valid task categories and monster types (from design doc)
VALID_TASK_CATEGORIES = ['errand', 'focus', 'physical', 'creative', 'social', 'wellness', 'organization']
VALID_MONSTER_TYPES = ['sloth', 'chaos', 'fog', 'burnout', 'stagnation', 'shadow', 'titan']

# Type effectiveness matrix (multiplier per monster_type × task_category)
TYPE_EFFECTIVENESS_MATRIX = {
    ('sloth', 'errand'): 1.5,
    ('sloth', 'focus'): 1.0,
    ('sloth', 'physical'): 1.5,
    ('sloth', 'creative'): 1.0,
    ('sloth', 'social'): 0.5,
    ('sloth', 'wellness'): 0.5,
    ('sloth', 'organization'): 1.0,

    ('chaos', 'errand'): 1.5,
    ('chaos', 'focus'): 0.5,
    ('chaos', 'physical'): 1.0,
    ('chaos', 'creative'): 0.5,
    ('chaos', 'social'): 1.0,
    ('chaos', 'wellness'): 1.0,
    ('chaos', 'organization'): 1.5,

    ('fog', 'errand'): 0.5,
    ('fog', 'focus'): 1.5,
    ('fog', 'physical'): 0.5,
    ('fog', 'creative'): 1.0,
    ('fog', 'social'): 1.0,
    ('fog', 'wellness'): 1.0,
    ('fog', 'organization'): 1.5,

    ('burnout', 'errand'): 1.0,
    ('burnout', 'focus'): 0.5,
    ('burnout', 'physical'): 1.0,
    ('burnout', 'creative'): 1.5,
    ('burnout', 'social'): 1.0,
    ('burnout', 'wellness'): 1.5,
    ('burnout', 'organization'): 0.5,

    ('stagnation', 'errand'): 0.5,
    ('stagnation', 'focus'): 1.0,
    ('stagnation', 'physical'): 1.0,
    ('stagnation', 'creative'): 1.5,
    ('stagnation', 'social'): 1.5,
    ('stagnation', 'wellness'): 1.0,
    ('stagnation', 'organization'): 0.5,

    ('shadow', 'errand'): 1.0,
    ('shadow', 'focus'): 1.0,
    ('shadow', 'physical'): 0.5,
    ('shadow', 'creative'): 0.5,
    ('shadow', 'social'): 1.5,
    ('shadow', 'wellness'): 1.5,
    ('shadow', 'organization'): 1.0,

    ('titan', 'errand'): 1.0,
    ('titan', 'focus'): 1.5,
    ('titan', 'physical'): 1.5,
    ('titan', 'creative'): 1.0,
    ('titan', 'social'): 0.5,
    ('titan', 'wellness'): 0.5,
    ('titan', 'organization'): 1.0,
}

# Expected monster type assignments (name -> type)
MONSTER_TYPE_ASSIGNMENTS = {
    # Easy Tier
    'Lazy Slime': 'sloth',
    'Snooze Sprite': 'sloth',
    'Distraction Rat': 'fog',
    'Excuse Imp': 'chaos',
    'Scroll Goblin': 'fog',
    'Couch Potato': 'sloth',
    'Notification Gremlin': 'fog',
    'I\'ll Do It Later Larry': 'stagnation',
    'The Snack Siren': 'burnout',
    'WiFi Vampire': 'shadow',

    # Medium Tier
    'Procrastination Goblin': 'sloth',
    'Netflix Naga': 'fog',
    'Comfort Zone Troll': 'stagnation',
    'Doom Scroller': 'fog',
    'Snack Attack Wolf': 'burnout',
    'YouTube Rabbit': 'fog',
    'Bed Gravity Bear': 'sloth',
    'Reply Guy Wraith': 'shadow',
    'Tabocalypse': 'chaos',
    'The Benchwarmer': 'stagnation',

    # Hard Tier
    'Burnout Specter': 'burnout',
    'Impostor Shade': 'shadow',
    'FOMO Phantom': 'shadow',
    'Perfectionism Knight': 'stagnation',
    'Analysis Paralysis': 'fog',
    'Scope Creep': 'chaos',
    'Meeting Minotaur': 'chaos',
    'Decision Fatigue Demon': 'burnout',
    'The Comparer': 'shadow',
    'Sunk Cost Succubus': 'stagnation',

    # Expert Tier
    'Anxiety Dragon': 'burnout',
    'Overwhelm Hydra': 'titan',
    'Comparison Demon': 'shadow',
    'The Infinite Backlog': 'titan',
    'Email Avalanche': 'chaos',
    'Context Switch Chimera': 'fog',
    'Imposter Syndrome Supreme': 'shadow',

    # Boss Tier
    'The Void of Inaction': 'stagnation',
    'Chaos Titan': 'chaos',
    'The Procrastinator King': 'sloth',
    'Existential Dread Lord': 'titan',
    'Burnout Phoenix': 'burnout',
}


@pytest.mark.skipif(not DB_AVAILABLE, reason="Database connection not available")
class TestTasksCategoryColumn:
    """Tests for the tasks.category column."""

    def test_category_column_exists(self):
        """Verify category column exists in tasks table."""
        conn = get_db_connection()
        if not conn:
            pytest.skip("No database connection")
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns
                    WHERE table_name = 'tasks'
                    AND column_name = 'category'
                );
            """)
            result = cursor.fetchone()
            assert result[0] is True, "category column does not exist in tasks table"
        finally:
            cursor.close()
            return_db_connection(conn)

    def test_category_default_value(self):
        """Verify category column has 'errand' as default."""
        conn = get_db_connection()
        if not conn:
            pytest.skip("No database connection")
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT column_default
                FROM information_schema.columns
                WHERE table_name = 'tasks'
                AND column_name = 'category';
            """)
            result = cursor.fetchone()
            assert result is not None, "category column not found"
            # Check default contains 'errand'
            assert 'errand' in str(result[0]), f"Expected default 'errand', got {result[0]}"
        finally:
            cursor.close()
            return_db_connection(conn)

    def test_category_check_constraint(self):
        """Verify category column has CHECK constraint for valid values."""
        conn = get_db_connection()
        if not conn:
            pytest.skip("No database connection")
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT pg_get_constraintdef(oid)
                FROM pg_constraint
                WHERE conrelid = 'tasks'::regclass
                AND conname LIKE '%category%';
            """)
            result = cursor.fetchone()
            assert result is not None, "No category constraint found"
            constraint_def = result[0]

            # Check all valid categories are in the constraint
            for category in VALID_TASK_CATEGORIES:
                assert category in constraint_def, f"Category '{category}' not in constraint"
        finally:
            cursor.close()
            return_db_connection(conn)

    def test_category_accepts_all_valid_values(self):
        """Verify all valid category values can be inserted."""
        conn = get_db_connection()
        if not conn:
            pytest.skip("No database connection")
        try:
            cursor = conn.cursor()

            # Create a test daily entry first
            cursor.execute("""
                INSERT INTO daily_entries (user_id, date, is_locked)
                VALUES ('00000000-0000-0000-0000-000000000000', CURRENT_DATE, false)
                ON CONFLICT DO NOTHING
                RETURNING id;
            """)
            result = cursor.fetchone()
            if result:
                entry_id = result[0]

                # Try inserting each valid category
                for category in VALID_TASK_CATEGORIES:
                    cursor.execute("""
                        INSERT INTO tasks (daily_entry_id, content, category)
                        VALUES (%s, %s, %s)
                        RETURNING id;
                    """, (entry_id, f"Test task {category}", category))
                    result = cursor.fetchone()
                    assert result is not None, f"Failed to insert task with category '{category}'"

                    # Clean up
                    cursor.execute("DELETE FROM tasks WHERE content = %s", (f"Test task {category}",))

                # Clean up daily entry
                cursor.execute("DELETE FROM daily_entries WHERE id = %s", (entry_id,))

                conn.commit()
        finally:
            cursor.close()
            return_db_connection(conn)

    def test_category_rejects_invalid_values(self):
        """Verify invalid category values are rejected."""
        conn = get_db_connection()
        if not conn:
            pytest.skip("No database connection")
        try:
            cursor = conn.cursor()

            # Create a test daily entry
            cursor.execute("""
                INSERT INTO daily_entries (user_id, date, is_locked)
                VALUES ('00000000-0000-0000-0000-000000000000', CURRENT_DATE, false)
                ON CONFLICT DO NOTHING
                RETURNING id;
            """)
            result = cursor.fetchone()
            if not result:
                pytest.skip("Could not create test daily entry")
            entry_id = result[0]

            # Try inserting an invalid category
            try:
                cursor.execute("""
                    INSERT INTO tasks (daily_entry_id, content, category)
                    VALUES (%s, %s, %s);
                """, (entry_id, "Invalid task", "invalid_category"))
                conn.commit()
                assert False, "Should have raised an error for invalid category"
            except Exception as e:
                # Expected to fail
                conn.rollback()
                assert 'category' in str(e).lower() or 'check' in str(e).lower()
            finally:
                # Clean up
                cursor.execute("DELETE FROM daily_entries WHERE id = %s", (entry_id,))
                conn.commit()
        finally:
            cursor.close()
            return_db_connection(conn)


@pytest.mark.skipif(not DB_AVAILABLE, reason="Database connection not available")
class TestMonstersTypeColumn:
    """Tests for the monsters.monster_type column."""

    def test_monster_type_column_exists(self):
        """Verify monster_type column exists in monsters table."""
        conn = get_db_connection()
        if not conn:
            pytest.skip("No database connection")
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns
                    WHERE table_name = 'monsters'
                    AND column_name = 'monster_type'
                );
            """)
            result = cursor.fetchone()
            assert result[0] is True, "monster_type column does not exist in monsters table"
        finally:
            cursor.close()
            return_db_connection(conn)

    def test_monster_type_is_not_null(self):
        """Verify monster_type column is NOT NULL."""
        conn = get_db_connection()
        if not conn:
            pytest.skip("No database connection")
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT is_nullable
                FROM information_schema.columns
                WHERE table_name = 'monsters'
                AND column_name = 'monster_type';
            """)
            result = cursor.fetchone()
            assert result is not None, "monster_type column not found"
            assert result[0] == 'NO', f"monster_type should be NOT NULL, got {result[0]}"
        finally:
            cursor.close()
            return_db_connection(conn)

    def test_monster_type_check_constraint(self):
        """Verify monster_type column has CHECK constraint for valid values."""
        conn = get_db_connection()
        if not conn:
            pytest.skip("No database connection")
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT pg_get_constraintdef(oid)
                FROM pg_constraint
                WHERE conrelid = 'monsters'::regclass
                AND conname LIKE '%monster_type%';
            """)
            result = cursor.fetchone()
            assert result is not None, "No monster_type constraint found"
            constraint_def = result[0]

            # Check all valid monster types are in the constraint
            for monster_type in VALID_MONSTER_TYPES:
                assert monster_type in constraint_def, f"Monster type '{monster_type}' not in constraint"
        finally:
            cursor.close()
            return_db_connection(conn)

    def test_all_monsters_have_type(self):
        """Verify all 42 monsters have a monster_type assigned."""
        conn = get_db_connection()
        if not conn:
            pytest.skip("No database connection")
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM monsters WHERE monster_type IS NULL;
            """)
            result = cursor.fetchone()
            assert result[0] == 0, f"{result[0]} monsters have NULL monster_type"
        finally:
            cursor.close()
            return_db_connection(conn)

    def test_monster_type_assignments_correct(self):
        """Verify each monster has the correct type assignment."""
        conn = get_db_connection()
        if not conn:
            pytest.skip("No database connection")
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name, monster_type FROM monsters ORDER BY name;
            """)
            results = cursor.fetchall()

            actual_types = {name: mtype for name, mtype in results}
            errors = []

            for monster_name, expected_type in MONSTER_TYPE_ASSIGNMENTS.items():
                actual_type = actual_types.get(monster_name)
                if actual_type != expected_type:
                    errors.append(f"{monster_name}: expected '{expected_type}', got '{actual_type}'")

            if errors:
                pytest.fail(f"Monster type mismatches:\n" + "\n".join(errors))
        finally:
            cursor.close()
            return_db_connection(conn)

    def test_monster_type_distribution(self):
        """Verify monster types are distributed reasonably across tiers."""
        conn = get_db_connection()
        if not conn:
            pytest.skip("No database connection")
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT monster_type, tier, COUNT(*) as count
                FROM monsters
                GROUP BY monster_type, tier
                ORDER BY tier, monster_type;
            """)
            results = cursor.fetchall()

            # Expected distribution from design doc
            expected = {
                ('sloth', 'easy'): 3, ('sloth', 'medium'): 2, ('sloth', 'boss'): 1,
                ('fog', 'easy'): 3, ('fog', 'medium'): 3, ('fog', 'hard'): 1, ('fog', 'expert'): 1,
                ('chaos', 'easy'): 1, ('chaos', 'medium'): 1, ('chaos', 'hard'): 2, ('chaos', 'expert'): 1, ('chaos', 'boss'): 1,
                ('burnout', 'easy'): 1, ('burnout', 'medium'): 1, ('burnout', 'hard'): 2, ('burnout', 'expert'): 1, ('burnout', 'boss'): 1,
                ('stagnation', 'easy'): 1, ('stagnation', 'medium'): 2, ('stagnation', 'hard'): 2, ('stagnation', 'boss'): 1,
                ('shadow', 'easy'): 1, ('shadow', 'medium'): 1, ('shadow', 'hard'): 3, ('shadow', 'expert'): 2,
                ('titan', 'expert'): 2, ('titan', 'boss'): 1,
            }

            actual = {(mtype, tier): count for mtype, tier, count in results}

            errors = []
            for key, expected_count in expected.items():
                actual_count = actual.get(key, 0)
                if actual_count != expected_count:
                    errors.append(f"{key}: expected {expected_count}, got {actual_count}")

            if errors:
                pytest.fail(f"Type distribution mismatches:\n" + "\n".join(errors))
        finally:
            cursor.close()
            return_db_connection(conn)


@pytest.mark.skipif(not DB_AVAILABLE, reason="Database connection not available")
class TestTypeEffectivenessTable:
    """Tests for the type_effectiveness table."""

    def test_table_exists(self):
        """Verify type_effectiveness table exists."""
        conn = get_db_connection()
        if not conn:
            pytest.skip("No database connection")
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'type_effectiveness'
                );
            """)
            result = cursor.fetchone()
            assert result[0] is True, "type_effectiveness table does not exist"
        finally:
            cursor.close()
            return_db_connection(conn)

    def test_table_has_correct_columns(self):
        """Verify type_effectiveness has all required columns."""
        conn = get_db_connection()
        if not conn:
            pytest.skip("No database connection")
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'type_effectiveness'
                ORDER BY ordinal_position;
            """)
            columns = {row[0] for row in cursor.fetchall()}

            required_columns = {'monster_type', 'task_category', 'multiplier'}
            assert required_columns == columns, f"Column mismatch. Expected: {required_columns}, Got: {columns}"
        finally:
            cursor.close()
            return_db_connection(conn)

    def test_has_49_rows(self):
        """Verify type_effectiveness has exactly 49 rows (7 types × 7 categories)."""
        conn = get_db_connection()
        if not conn:
            pytest.skip("No database connection")
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM type_effectiveness;")
            result = cursor.fetchone()
            assert result[0] == 49, f"Expected 49 rows, got {result[0]}"
        finally:
            cursor.close()
            return_db_connection(conn)

    def test_multiplier_values_valid(self):
        """Verify all multiplier values are 0.5, 1.0, or 1.5."""
        conn = get_db_connection()
        if not conn:
            pytest.skip("No database connection")
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT multiplier FROM type_effectiveness ORDER BY multiplier;
            """)
            results = [row[0] for row in cursor.fetchall()]
            expected = [0.5, 1.0, 1.5]
            assert results == expected, f"Expected multipliers {expected}, got {results}"
        finally:
            cursor.close()
            return_db_connection(conn)

    def test_effectiveness_matrix_correct(self):
        """Verify the complete effectiveness matrix matches design."""
        conn = get_db_connection()
        if not conn:
            pytest.skip("No database connection")
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT monster_type, task_category, multiplier
                FROM type_effectiveness;
            """)
            results = cursor.fetchall()

            actual = {(mt, tc): mult for mt, tc, mult in results}
            errors = []

            for key, expected_multiplier in TYPE_EFFECTIVENESS_MATRIX.items():
                actual_multiplier = actual.get(key)
                if actual_multiplier != expected_multiplier:
                    errors.append(f"{key}: expected {expected_multiplier}, got {actual_multiplier}")

            if errors:
                pytest.fail(f"Effectiveness matrix mismatches:\n" + "\n".join(errors))
        finally:
            cursor.close()
            return_db_connection(conn)

    def test_primary_key_constraint(self):
        """Verify (monster_type, task_category) is the primary key."""
        conn = get_db_connection()
        if not conn:
            pytest.skip("No database connection")
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT a.attname
                FROM pg_index i
                JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
                WHERE i.indrelid = 'type_effectiveness'::regclass
                AND i.indisprimary;
            """)
            pk_columns = {row[0] for row in cursor.fetchall()}

            expected_pk = {'monster_type', 'task_category'}
            assert pk_columns == expected_pk, f"PK mismatch. Expected: {expected_pk}, Got: {pk_columns}"
        finally:
            cursor.close()
            return_db_connection(conn)


@pytest.mark.skipif(not DB_AVAILABLE, reason="Database connection not available")
class TestTypeDiscoveriesTable:
    """Tests for the type_discoveries table."""

    def test_table_exists(self):
        """Verify type_discoveries table exists."""
        conn = get_db_connection()
        if not conn:
            pytest.skip("No database connection")
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'type_discoveries'
                );
            """)
            result = cursor.fetchone()
            assert result[0] is True, "type_discoveries table does not exist"
        finally:
            cursor.close()
            return_db_connection(conn)

    def test_table_has_correct_columns(self):
        """Verify type_discoveries has all required columns."""
        conn = get_db_connection()
        if not conn:
            pytest.skip("No database connection")
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'type_discoveries'
                ORDER BY ordinal_position;
            """)
            columns = {row[0] for row in cursor.fetchall()}

            required_columns = {
                'id', 'user_id', 'monster_type', 'task_category',
                'effectiveness', 'discovered_at'
            }
            assert required_columns.issubset(columns), f"Missing columns: {required_columns - columns}"
        finally:
            cursor.close()
            return_db_connection(conn)

    def test_effectiveness_check_constraint(self):
        """Verify effectiveness column has CHECK constraint."""
        conn = get_db_connection()
        if not conn:
            pytest.skip("No database connection")
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT pg_get_constraintdef(oid)
                FROM pg_constraint
                WHERE conrelid = 'type_discoveries'::regclass
                AND conname LIKE '%effectiveness%';
            """)
            result = cursor.fetchone()
            assert result is not None, "No effectiveness constraint found"
            constraint_def = result[0]

            valid_values = ['super_effective', 'neutral', 'resisted']
            for value in valid_values:
                assert value in constraint_def, f"Effectiveness value '{value}' not in constraint"
        finally:
            cursor.close()
            return_db_connection(conn)

    def test_unique_constraint(self):
        """Verify (user_id, monster_type, task_category) is unique."""
        conn = get_db_connection()
        if not conn:
            pytest.skip("No database connection")
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT a.attname
                FROM pg_constraint c
                JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = ANY(c.conkey)
                WHERE c.conrelid = 'type_discoveries'::regclass
                AND c.contype = 'u';
            """)
            unique_columns = {row[0] for row in cursor.fetchall()}

            expected_unique = {'user_id', 'monster_type', 'task_category'}
            assert unique_columns == expected_unique, f"Unique constraint mismatch. Expected: {expected_unique}, Got: {unique_columns}"
        finally:
            cursor.close()
            return_db_connection(conn)

    def test_user_id_foreign_key(self):
        """Verify user_id references profiles(id) with CASCADE delete."""
        conn = get_db_connection()
        if not conn:
            pytest.skip("No database connection")
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT pg_get_constraintdef(oid)
                FROM pg_constraint
                WHERE conrelid = 'type_discoveries'::regclass
                AND conname LIKE '%user_id%';
            """)
            result = cursor.fetchone()
            assert result is not None, "No user_id foreign key found"
            constraint_def = result[0]

            assert 'profiles' in constraint_def, "FK doesn't reference profiles"
            assert 'CASCADE' in constraint_def, "FK doesn't have ON DELETE CASCADE"
        finally:
            cursor.close()
            return_db_connection(conn)

    def test_index_exists(self):
        """Verify idx_type_discoveries_user_monster index exists."""
        conn = get_db_connection()
        if not conn:
            pytest.skip("No database connection")
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM pg_indexes
                    WHERE tablename = 'type_discoveries'
                    AND indexname = 'idx_type_discoveries_user_monster'
                );
            """)
            result = cursor.fetchone()
            assert result[0] is True, "idx_type_discoveries_user_monster index does not exist"
        finally:
            cursor.close()
            return_db_connection(conn)


@pytest.mark.skipif(not DB_AVAILABLE, reason="Database connection not available")
class TestTypeEffectivenessRLS:
    """Tests for RLS policies on new tables."""

    def test_type_effectiveness_rls_enabled(self):
        """Verify RLS is enabled on type_effectiveness."""
        conn = get_db_connection()
        if not conn:
            pytest.skip("No database connection")
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT relrowsecurity
                FROM pg_class
                WHERE relname = 'type_effectiveness';
            """)
            result = cursor.fetchone()
            assert result is not None, "type_effectiveness table not found"
            assert result[0] is True, "RLS not enabled on type_effectiveness"
        finally:
            cursor.close()
            return_db_connection(conn)

    def test_type_effectiveness_public_read_policy(self):
        """Verify type_effectiveness has public read policy."""
        conn = get_db_connection()
        if not conn:
            pytest.skip("No database connection")
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM pg_policies
                    WHERE tablename = 'type_effectiveness'
                    AND policyname = 'Type effectiveness is viewable by everyone'
                );
            """)
            result = cursor.fetchone()
            assert result[0] is True, "Public read policy does not exist for type_effectiveness"
        finally:
            cursor.close()
            return_db_connection(conn)

    def test_type_discoveries_rls_enabled(self):
        """Verify RLS is enabled on type_discoveries."""
        conn = get_db_connection()
        if not conn:
            pytest.skip("No database connection")
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT relrowsecurity
                FROM pg_class
                WHERE relname = 'type_discoveries';
            """)
            result = cursor.fetchone()
            assert result is not None, "type_discoveries table not found"
            assert result[0] is True, "RLS not enabled on type_discoveries"
        finally:
            cursor.close()
            return_db_connection(conn)

    def test_type_discoveries_policies_exist(self):
        """Verify type_discoveries has expected RLS policies."""
        conn = get_db_connection()
        if not conn:
            pytest.skip("No database connection")
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT policyname
                FROM pg_policies
                WHERE tablename = 'type_discoveries';
            """)
            policies = {row[0] for row in cursor.fetchall()}

            expected_policies = {
                'Users can view their own discoveries',
                'Users can insert their own discoveries'
            }
            assert expected_policies.issubset(policies), f"Missing policies: {expected_policies - policies}"
        finally:
            cursor.close()
            return_db_connection(conn)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
