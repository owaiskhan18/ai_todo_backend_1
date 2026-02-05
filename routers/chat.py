# backend/routers/chat.py
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Dict, Any, List, Optional

import google.genai as genai  # ✅ Correct SDK

from services.auth import get_current_user
from models.user import User
from config import settings
from core.ai_tools import run_ai_tool
from sqlmodel import Session
from database import get_session

router = APIRouter(prefix="/chat", tags=["chat"])

# Initialize Gemini client
client = genai.Client(api_key=settings.GEMINI_API_KEY)

# In‑memory conversation history per user
conversation_sessions: Dict[str, Any] = {}


class ChatMessageRequest(BaseModel):
    message: str


class ChatMessageResponse(BaseModel):
    reply: str
    task_created: Optional[bool] = False
    task_id: Optional[str] = None


@router.post("/", response_model=ChatMessageResponse)
async def chat_with_ai(
    *,
    session: Session = Depends(get_session),
    request: ChatMessageRequest,
    current_user: User = Depends(get_current_user)
):
    user_id = str(current_user.id)

    try:
        # Create or reuse a chat session
        if user_id not in conversation_sessions:
            # new chat session
            chat = client.chats.create(model="gemini-2.5-flash")
            conversation_sessions[user_id] = chat
        else:
            chat = conversation_sessions[user_id]

        # send the user message to the chat session
        response = chat.send_message(request.message)

        ai_reply = response.text or "Done ✅"
        task_created = False
        task_id = None

        # You could parse the reply here if you expect tool / task calls
        # Example (if your tool returns JSON from the AI):
        # if "create_task" in ai_reply:
        #     task_created = True
        #     task_id = "some_id"

        return ChatMessageResponse(
            reply=ai_reply,
            task_created=task_created,
            task_id=task_id,
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
