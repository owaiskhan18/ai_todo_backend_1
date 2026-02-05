# backend/crud/task.py
from sqlmodel import Session, select
from models.task import Task, Priority
from schemas.task import TaskCreate, TaskUpdate
from typing import List, Optional
from uuid import uuid4 # Using uuid for task IDs as per frontend Task interface (string id)

def get_tasks(
    session: Session,
    user_id: str,
    title: Optional[str] = None,
    due_date: Optional[str] = None, # Expect YYYY-MM-DD
    priority: Optional[Priority] = None
) -> List[Task]:
    statement = select(Task).where(Task.user_id == user_id)
    if title:
        statement = statement.where(Task.title.ilike(f"%{title}%")) # Case-insensitive search
    if due_date:
        # For date filtering, compare date parts. Assuming due_date in DB is datetime.
        # This will need careful handling depending on exact DB schema and desired comparison
        statement = statement.where(Task.due_date == due_date) # Simplified for example
    if priority:
        statement = statement.where(Task.priority == priority)
        
    return session.exec(statement).all()

def create_task(session: Session, task_create: TaskCreate, user_id: str) -> Task:
    # Using UUID for task ID as per frontend Task interface, SQLModel will handle string conversion for PK if needed or adjust model
    db_task = Task(id=str(uuid4()), **task_create.model_dump(), user_id=user_id)
    session.add(db_task)
    session.commit()
    session.refresh(db_task)
    return db_task

def get_task_by_id(session: Session, task_id: str, user_id: str) -> Optional[Task]:
    statement = select(Task).where(Task.id == task_id, Task.user_id == user_id)
    return session.exec(statement).first()

def update_task(session: Session, db_task: Task, task_update: TaskUpdate) -> Task:
    task_data = task_update.model_dump(exclude_unset=True)
    for key, value in task_data.items():
        setattr(db_task, key, value)
    session.add(db_task)
    session.commit()
    session.refresh(db_task)
    return db_task

def delete_task(session: Session, db_task: Task):
    session.delete(db_task)
    session.commit()