# backend/schemas/task.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from models.task import Priority # Import Priority Enum

class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    priority: Priority = Priority.MEDIUM
    due_date: Optional[datetime] = None
    enable_reminder: bool = False

class TaskCreate(TaskBase):
    pass

class TaskUpdate(TaskBase):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[Priority] = None
    due_date: Optional[datetime] = None
    enable_reminder: Optional[bool] = None

class TaskResponse(TaskBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True # for SQLModel