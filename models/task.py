# backend/models/task.py
from typing import Optional
from datetime import datetime
from sqlmodel import Field, Relationship, SQLModel
from enum import Enum as PyEnum

class Priority(str, PyEnum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"

class Task(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: Optional[str] = None
    priority: Priority = Priority.MEDIUM
    due_date: Optional[datetime] = None
    enable_reminder: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    user_id: int = Field(foreign_key="user.id")
    owner: "User" = Relationship(back_populates="tasks")