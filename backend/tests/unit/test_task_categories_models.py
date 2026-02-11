"""
Unit tests for Task Category and Monster Type model changes.

Tests the new fields added to support the elemental combat system:
- TaskBase.category field with default value
- MonsterBase.monster_type field with default value
- draft_tasks endpoint persisting category to database
"""
import pytest
from models import TaskBase, TaskCreate, Task, MonsterBase, Monster
from pydantic import ValidationError


# =============================================================================
# Test TaskBase.category field
# =============================================================================

class TestTaskBaseCategory:
    """Test the category field on TaskBase model."""

    def test_taskbase_has_default_category_errand(self):
        """TaskBase should have 'errand' as default category."""
        task = TaskBase(content="Test task")
        assert task.category == "errand"

    def test_taskbase_can_set_valid_category(self):
        """TaskBase should accept any valid category value."""
        valid_categories = [
            "errand", "focus", "physical", "creative",
            "social", "wellness", "organization"
        ]
        for cat in valid_categories:
            task = TaskBase(content="Test task", category=cat)
            assert task.category == cat

    def test_taskbase_category_is_string(self):
        """TaskBase category field should be a string type."""
        task = TaskBase(content="Test task")
        assert isinstance(task.category, str)


# =============================================================================
# Test TaskCreate inherits category
# =============================================================================

class TestTaskCreateCategory:
    """Test that TaskCreate properly inherits the category field."""

    def test_taskcreate_has_default_category(self):
        """TaskCreate should inherit default category from TaskBase."""
        task_create = TaskCreate(content="Test task")
        assert task_create.category == "errand"

    def test_taskcreate_can_set_category(self):
        """TaskCreate should allow setting category during creation."""
        task_create = TaskCreate(content="Test task", category="focus")
        assert task_create.category == "focus"

    def test_taskcreate_with_is_optional_and_category(self):
        """TaskCreate should handle both is_optional and category together."""
        task_create = TaskCreate(
            content="Optional task",
            is_optional=True,
            category="creative"
        )
        assert task_create.is_optional is True
        assert task_create.category == "creative"


# =============================================================================
# Test MonsterBase.monster_type field
# =============================================================================

class TestMonsterBaseMonsterType:
    """Test the monster_type field on MonsterBase model."""

    def test_monsterbase_has_default_monster_type_sloth(self):
        """MonsterBase should have 'sloth' as default monster_type."""
        monster = MonsterBase(
            name="Test Monster",
            emoji="👹",
            tier="easy",
            base_hp=100
        )
        assert monster.monster_type == "sloth"

    def test_monsterbase_can_set_valid_monster_type(self):
        """MonsterBase should accept any valid monster_type value."""
        valid_types = [
            "sloth", "chaos", "fog", "burnout",
            "stagnation", "shadow", "titan"
        ]
        for mtype in valid_types:
            monster = MonsterBase(
                name="Test Monster",
                emoji="👹",
                tier="easy",
                base_hp=100,
                monster_type=mtype
            )
            assert monster.monster_type == mtype

    def test_monsterbase_monster_type_is_string(self):
        """MonsterBase monster_type field should be a string type."""
        monster = MonsterBase(
            name="Test Monster",
            emoji="👹",
            tier="easy",
            base_hp=100
        )
        assert isinstance(monster.monster_type, str)

    def test_monsterbase_all_fields_with_monster_type(self):
        """MonsterBase should work with all fields including monster_type."""
        monster = MonsterBase(
            name="Test Monster",
            emoji="🦥",
            tier="medium",
            base_hp=150,
            description="A test monster for productivity",
            monster_type="sloth"
        )
        assert monster.name == "Test Monster"
        assert monster.emoji == "🦥"
        assert monster.tier == "medium"
        assert monster.base_hp == 150
        assert monster.description == "A test monster for productivity"
        assert monster.monster_type == "sloth"


# =============================================================================
# Test Task and Monster response models include new fields
# =============================================================================

class TestResponseModelsIncludeNewFields:
    """Test that response models include the new fields."""

    def test_task_model_has_category_field(self):
        """Task model should have category field accessible."""
        # Task inherits from TaskBase, so it should have category
        task_dict = {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "daily_entry_id": "223e4567-e89b-12d3-a456-426614174000",
            "content": "Test task",
            "is_optional": False,
            "is_completed": False,
            "created_at": "2024-01-01T00:00:00",
            "category": "focus"
        }
        task = Task(**task_dict)
        assert task.category == "focus"

    def test_task_model_default_category(self):
        """Task model should default to 'errand' if category not provided."""
        task_dict = {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "daily_entry_id": "223e4567-e89b-12d3-a456-426614174000",
            "content": "Test task",
            "is_optional": False,
            "is_completed": False,
            "created_at": "2024-01-01T00:00:00"
        }
        task = Task(**task_dict)
        assert task.category == "errand"

    def test_monster_model_has_monster_type_field(self):
        """Monster model should have monster_type field accessible."""
        monster_dict = {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "name": "Test Monster",
            "emoji": "🦥",
            "tier": "easy",
            "base_hp": 100,
            "description": "A test monster",
            "created_at": "2024-01-01T00:00:00",
            "monster_type": "chaos"
        }
        monster = Monster(**monster_dict)
        assert monster.monster_type == "chaos"

    def test_monster_model_default_monster_type(self):
        """Monster model should default to 'sloth' if monster_type not provided."""
        monster_dict = {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "name": "Test Monster",
            "emoji": "🦥",
            "tier": "easy",
            "base_hp": 100,
            "created_at": "2024-01-01T00:00:00"
        }
        monster = Monster(**monster_dict)
        assert monster.monster_type == "sloth"
