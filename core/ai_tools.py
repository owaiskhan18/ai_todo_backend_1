import google.genai as genai
from google.genai import types
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlmodel import Session
from pydantic import BaseModel, Field

from crud.task import create_task, get_tasks, update_task, delete_task, get_task_by_id
from schemas.task import TaskCreate, TaskUpdate, TaskResponse, Priority


# =====================================================
# 🔹 Gemini Tool Schemas (ONLY SIMPLE TYPES)
# =====================================================

class CreateTaskToolArgs(BaseModel):
    title: str = Field(..., description="The title of the task")
    description: Optional[str] = Field(None, description="Detailed description")
    priority: Optional[str] = Field(
        "Medium",
        description="Low, Medium, or High"
    )
    due_date: Optional[str] = Field(
        None,
        description="YYYY-MM-DD"
    )
    enable_reminder: Optional[bool] = Field(False)


class UpdateTaskToolArgs(BaseModel):
    task_id: str = Field(..., description="Task ID")
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = Field(
        None,
        description="Low, Medium, or High"
    )
    due_date: Optional[str] = Field(None, description="YYYY-MM-DD")
    enable_reminder: Optional[bool] = None


class DeleteTaskToolArgs(BaseModel):
    task_id: str = Field(..., description="Task ID")


class ListTasksToolArgs(BaseModel):
    title: Optional[str] = None
    due_date: Optional[str] = None
    priority: Optional[str] = Field(
        None,
        description="Low, Medium, or High"
    )


# =====================================================
# 🔹 Tool Functions
# =====================================================

async def create_task_tool_func(
    session: Session,
    user_id: int,
    title: str,
    description: Optional[str] = None,
    priority: Optional[str] = "Medium",
    due_date: Optional[str] = None,
    enable_reminder: bool = False,
) -> Dict[str, Any]:

    # --- Priority ---
    try:
        priority_enum = Priority[priority.upper()]
    except Exception:
        return {"error": "Priority must be Low, Medium, or High"}

    # --- Due date ---
    due_date_dt = None
    if due_date:
        try:
            due_date_dt = datetime.strptime(due_date, "%Y-%m-%d")
        except ValueError:
            return {"error": "Invalid date format. Use YYYY-MM-DD"}

    task_create = TaskCreate(
        title=title,
        description=description,
        priority=priority_enum,
        due_date=due_date_dt,
        enable_reminder=enable_reminder,
    )

    db_task = create_task(session, task_create, user_id)
    return TaskResponse.model_validate(db_task).model_dump(mode="json")


async def list_tasks_tool_func(
    session: Session,
    user_id: int,
    title: Optional[str] = None,
    due_date: Optional[str] = None,
    priority: Optional[str] = None,
) -> List[Dict[str, Any]]:

    priority_enum = None
    if priority:
        try:
            priority_enum = Priority[priority.upper()]
        except Exception:
            return {"error": "Priority must be Low, Medium, or High"}

    tasks = get_tasks(
        session,
        user_id=user_id,
        title=title,
        due_date=due_date,
        priority=priority_enum,
    )

    return [
        TaskResponse.model_validate(task).model_dump(mode="json")
        for task in tasks
    ]


async def update_task_tool_func(
    session: Session,
    user_id: int,
    task_id: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    priority: Optional[str] = None,
    due_date: Optional[str] = None,
    enable_reminder: Optional[bool] = None,
) -> Dict[str, Any]:

    try:
        task_id_int = int(task_id)
    except ValueError:
        return {"error": "Task ID must be integer"}

    db_task = get_task_by_id(session, task_id_int, user_id)
    if not db_task:
        return {"error": "Task not found"}

    updates = {}

    if title is not None:
        updates["title"] = title
    if description is not None:
        updates["description"] = description
    if enable_reminder is not None:
        updates["enable_reminder"] = enable_reminder

    if priority:
        try:
            updates["priority"] = Priority[priority.upper()]
        except Exception:
            return {"error": "Priority must be Low, Medium, or High"}

    if due_date:
        try:
            updates["due_date"] = datetime.strptime(due_date, "%Y-%m-%d")
        except ValueError:
            return {"error": "Invalid date format"}

    task_update = TaskUpdate(**updates)
    updated_task = update_task(session, db_task, task_update)

    return TaskResponse.model_validate(updated_task).model_dump(mode="json")


async def delete_task_tool_func(
    session: Session,
    user_id: int,
    task_id: str,
) -> Dict[str, Any]:

    try:
        task_id_int = int(task_id)
    except ValueError:
        return {"error": "Task ID must be integer"}

    db_task = get_task_by_id(session, task_id_int, user_id)
    if not db_task:
        return {"error": "Task not found"}

    delete_task(session, db_task)
    return {"message": f"Task '{db_task.title}' deleted"}


# =====================================================
# 🔹 Tool Map
# =====================================================

ai_tool_map = {
    "create_task": create_task_tool_func,
    "list_tasks": list_tasks_tool_func,
    "update_task": update_task_tool_func,
    "delete_task": delete_task_tool_func,
}


# =====================================================
# 🔹 Gemini Tool Declarations (NO CLEANING NEEDED)
# =====================================================

available_tools_for_gemini = [
    types.Tool(function_declarations=[
        types.FunctionDeclaration(
            name="create_task",
            description="Create a task",
            parameters=CreateTaskToolArgs.model_json_schema(),
        )
    ]),
    types.Tool(function_declarations=[
        types.FunctionDeclaration(
            name="list_tasks",
            description="List tasks",
            parameters=ListTasksToolArgs.model_json_schema(),
        )
    ]),
    types.Tool(function_declarations=[
        types.FunctionDeclaration(
            name="update_task",
            description="Update a task",
            parameters=UpdateTaskToolArgs.model_json_schema(),
        )
    ]),
    types.Tool(function_declarations=[
        types.FunctionDeclaration(
            name="delete_task",
            description="Delete a task",
            parameters=DeleteTaskToolArgs.model_json_schema(),
        )
    ]),
]


# =====================================================
# 🔹 Tool Runner
# =====================================================

async def run_ai_tool(
    tool_name: str,
    args: Dict[str, Any],
    user_id: str,
    session: Session,
) -> Dict[str, Any]:

    tool_func = ai_tool_map.get(tool_name)
    if not tool_func:
        return {"error": "Tool not found"}

    try:
        user_id_int = int(user_id)
    except ValueError:
        return {"error": "Invalid user ID"}

    return await tool_func(
        session=session,
        user_id=user_id_int,
        **args,
    )
