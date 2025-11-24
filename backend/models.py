from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime
from uuid import UUID

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
    battle_id: UUID
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
