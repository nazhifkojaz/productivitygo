from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime
from uuid import UUID

# Import GameMode enum for type hints
from utils.enums import GameMode

# --- PROFILES ---
class ProfileBase(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    level: int = 1
    exp: int = 0
    timezone: str = "UTC"

class Profile(ProfileBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True

# --- TASKS ---
class TaskBase(BaseModel):
    content: str
    is_optional: bool = False

class TaskCreate(TaskBase):
    pass

class Task(TaskBase):
    id: UUID
    daily_entry_id: UUID
    is_completed: bool = False
    proof_url: Optional[str] = None
    assigned_score: int = 0
    created_at: datetime

    class Config:
        from_attributes = True

# --- DAILY ENTRIES ---
class DailyEntryBase(BaseModel):
    date: date
    is_locked: bool = False

class DailyEntry(DailyEntryBase):
    id: UUID
    # REFACTOR-003: battle_id will become Optional when adventure mode is added
    # For now, it's required and links to the active battle
    battle_id: UUID
    # adventure_id: Optional[UUID] = None  # TODO: Add for adventure mode
    user_id: UUID
    score_distribution: Optional[List[int]] = None
    day_winner: Optional[bool] = None
    created_at: datetime
    tasks: List[Task] = []

    class Config:
        from_attributes = True

# --- BATTLES ---
class BattleBase(BaseModel):
    start_date: date
    end_date: date
    status: str = "active"

class Battle(BattleBase):
    id: UUID
    user1_id: UUID
    user2_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True

# --- MONSTERS ---
class MonsterBase(BaseModel):
    name: str
    emoji: str = "👹"
    tier: str  # easy, medium, hard, expert, boss
    base_hp: int
    description: Optional[str] = None


class Monster(MonsterBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


# --- ADVENTURES ---
class AdventureBase(BaseModel):
    duration: int
    start_date: date
    deadline: date
    status: str = "active"


class Adventure(AdventureBase):
    id: UUID
    user_id: UUID
    monster_id: UUID
    monster_max_hp: int
    monster_current_hp: int
    current_round: int = 0
    total_damage_dealt: int = 0
    xp_earned: int = 0
    break_days_used: int = 0
    max_break_days: int = 2
    is_on_break: bool = False
    break_end_date: Optional[date] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True
