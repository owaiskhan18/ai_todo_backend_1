# backend/routers/chat.py
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Dict, Any, List, Optional

from google import genai

from services.auth import get_current_user
from models.user import User
from config import settings
from core.ai_tools import available_tools_for_gemini, run_ai_tool
from sqlmodel import Session
from database import get_session

router = APIRouter(prefix="/chat", tags=["chat"])

# ✅ Gemini client
client = genai.Client(api_key=settings.GEMINI_API_KEY)

# Simple in-memory conversation history
conversation_history: Dict[str, List[Dict[str, Any]]] = {}


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

    if user_id not in conversation_history:
        conversation_history[user_id] = []

    try:
        # Build conversation for Gemini
        contents = conversation_history[user_id] + [
            {"role": "user", "parts": [{"text": request.message}]}
        ]

        # ✅ Use a valid Gemini 2.5 model
        response = client.models.generate_content(
            model="models/gemini-2.5-flash",  # Updated model
            contents=contents,
        )

        ai_reply = ""
        task_created = False
        task_id = None

        # ✅ Parse response safely
        if response.candidates:
            for candidate in response.candidates:
                for part in candidate.content.parts:
                    # Normal text reply
                    if getattr(part, "text", None):
                        ai_reply += part.text

                    # Tool call
                    if getattr(part, "function_call", None):
                        fc = part.function_call
                        tool_name = fc.name
                        tool_args = dict(fc.args) if fc.args else {}

                        tool_result = await run_ai_tool(
                            tool_name=tool_name,
                            args=tool_args,
                            user_id=user_id,
                            session=session,
                        )

                        ai_reply += f"\n\n{tool_result}"

                        if tool_name == "create_task" and isinstance(tool_result, dict):
                            task_created = True
                            task_id = str(tool_result.get("id"))

        # Save conversation
        conversation_history[user_id].append(
            {"role": "user", "parts": [{"text": request.message}]}
        )
        conversation_history[user_id].append(
            {"role": "model", "parts": [{"text": ai_reply}]}
        )

        return ChatMessageResponse(
            reply=ai_reply or "Done ✅",
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
