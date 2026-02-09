
# backend/routers/chat.py

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Dict, Any
from datetime import datetime

import google.genai as genai  # Official SDK

from services.auth import get_current_user
from models.user import User
from models.task import Task
from config import settings
from sqlmodel import Session
from database import get_session

router = APIRouter(prefix="/chat", tags=["chat"])

# Initialize Gemini client
client = genai.Client(api_key=settings.GEMINI_API_KEY)

# Conversation sessions per user
conversation_sessions: Dict[str, Any] = {}

# Track task creation state per user
task_creation_sessions: Dict[str, Dict[str, Any]] = {}

# Allowed ENUM priorities in DB
VALID_PRIORITIES = {"Low", "Medium", "High"}


class ChatMessageRequest(BaseModel):
    message: str


class ChatMessageResponse(BaseModel):
    reply: str


@router.post("/", response_model=ChatMessageResponse)
async def chat_with_ai(
    *,
    session: Session = Depends(get_session),
    request: ChatMessageRequest,
    current_user: User = Depends(get_current_user)
):
    user_id = str(current_user.id)

    try:
        # --- Create or reuse chat session ---
        if user_id not in conversation_sessions:
            chat_session = client.chats.create(model="gemini-2.5-flash")
            conversation_sessions[user_id] = chat_session
        else:
            chat_session = conversation_sessions[user_id]

        # --- Check if user is in task creation flow ---
        if user_id in task_creation_sessions:
            task_data = task_creation_sessions[user_id]

            # Step 1: Collect Title
            if "title" not in task_data:
                task_data["title"] = request.message.strip()
                return ChatMessageResponse(reply="Got it! Now provide the task description:")

            # Step 2: Collect Description
            if "description" not in task_data:
                task_data["description"] = request.message.strip()
                return ChatMessageResponse(
                    reply=f"Great! Set the priority for this task (Low, Medium, High):"
                )

            # Step 3: Collect Priority
            if "priority" not in task_data:
                priority = request.message.strip().capitalize()
                if priority not in VALID_PRIORITIES:
                    return ChatMessageResponse(
                        reply="Invalid priority. Please enter one of: Low, Medium, High"
                    )
                task_data["priority"] = priority

                # --- All data collected, save to DB ---
                ai_task = Task(
                    title=task_data["title"][:100],
                    description=task_data["description"][:500],
                    user_id=current_user.id,
                    priority=task_data["priority"],
                    created_at=datetime.utcnow(),
                    due_date=None,
                    enable_reminder=False,
                )
                session.add(ai_task)
                session.commit()
                session.refresh(ai_task)

                # Clear task creation session
                del task_creation_sessions[user_id]

                return ChatMessageResponse(
                    reply=f"Task '{ai_task.title}' added successfully!"
                )

        # --- Normal chat flow ---
        message_text = request.message.strip().lower()

        # Trigger task creation if user says "add task"
        if "add task" in message_text:
            task_creation_sessions[user_id] = {}  # start task creation flow
            return ChatMessageResponse(reply="Sure! Let's create a new task. What is the task title?")

        # Otherwise, send message to AI
        response = chat_session.send_message(request.message)
        reply_text = response.text or "No reply from AI"

        return ChatMessageResponse(reply=reply_text)

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
