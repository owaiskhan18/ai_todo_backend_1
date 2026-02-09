# backend/crud/task.py
from sqlmodel import Session, select
from models.task import Task, Priority
from schemas.task import TaskCreate, TaskUpdate
from typing import List, Optional
# Removed uuid import as task IDs are now integers

def get_tasks(
    session: Session,
    user_id: int, # Changed to int
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

def create_task(session: Session, task_create: TaskCreate, user_id: int) -> Task: # Changed user_id to int
    # Task ID is auto-incremented integer, so no need to pass id explicitly
    db_task = Task(**task_create.model_dump(), user_id=user_id)
    session.add(db_task)
    session.commit()
    session.refresh(db_task)
    return db_task

def get_task_by_id(session: Session, task_id: int, user_id: int) -> Optional[Task]: # Changed task_id and user_id to int
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