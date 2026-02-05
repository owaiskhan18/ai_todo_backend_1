# backend/routers/tasks.py
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session
from typing import List, Optional
from datetime import datetime

from database import get_session
from crud.task import create_task, get_tasks, get_task_by_id, update_task, delete_task
from schemas.task import TaskCreate, TaskUpdate, TaskResponse, Priority
from services.auth import get_current_user
from models.user import User

router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_new_task(
    *, 
    session: Session = Depends(get_session), 
    task_create: TaskCreate, 
    current_user: User = Depends(get_current_user)
):
    # Ensure due_date is treated as UTC if provided without timezone info
    if task_create.due_date and task_create.due_date.tzinfo is None:
        task_create.due_date = task_create.due_date.replace(tzinfo=datetime.utcnow().tzinfo)

    db_task = create_task(session, task_create, user_id=current_user.id)
    return db_task

@router.get("/", response_model=List[TaskResponse])
def read_tasks(
    *, 
    session: Session = Depends(get_session), 
    current_user: User = Depends(get_current_user),
    title: Optional[str] = Query(None, description="Filter tasks by title"),
    due_date: Optional[str] = Query(None, description="Filter tasks by due date (YYYY-MM-DD)"),
    priority: Optional[Priority] = Query(None, description="Filter tasks by priority")
):
    tasks = get_tasks(session, user_id=current_user.id, title=title, due_date=due_date, priority=priority)
    return tasks

@router.get("/{task_id}", response_model=TaskResponse)
def read_task(
    *, 
    session: Session = Depends(get_session), 
    task_id: int, 
    current_user: User = Depends(get_current_user)
):
    task = get_task_by_id(session, task_id, user_id=current_user.id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task

@router.put("/{task_id}", response_model=TaskResponse)
def update_existing_task(
    *, 
    session: Session = Depends(get_session), 
    task_id: int, 
    task_update: TaskUpdate, 
    current_user: User = Depends(get_current_user)
):
    db_task = get_task_by_id(session, task_id, user_id=current_user.id)
    if not db_task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    
    # Ensure due_date is treated as UTC if provided without timezone info
    if task_update.due_date and task_update.due_date.tzinfo is None:
        task_update.due_date = task_update.due_date.replace(tzinfo=datetime.utcnow().tzinfo)

    task = update_task(session, db_task, task_update)
    return task

@router.delete("/{task_id}", status_code=status.HTTP_200_OK)
def delete_existing_task(
    *, 
    session: Session = Depends(get_session), 
    task_id: int, 
    current_user: User = Depends(get_current_user)
):
    db_task = get_task_by_id(session, task_id, user_id=current_user.id)
    if not db_task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    
    delete_task(session, db_task)
    return {"message": "Task deleted successfully"}