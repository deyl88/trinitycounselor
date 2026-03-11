"""
Agent A API routes — Private Counselor for Partner A.

Endpoints:
  POST /agent-a/chat    — send a message, receive a response

Only the authenticated user (Partner A) can access these endpoints.
Partner B and all other users are rejected by the auth middleware.
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.agents import agent_a
from backend.api.middleware.auth import get_current_user
from backend.db.postgres import get_session
from backend.memory.conversation_store import save_message
from backend.models.message import MessageRole
from backend.models.session import Session, SessionStatus, SessionType
from backend.models.user import User
from sqlalchemy import select

router = APIRouter()


class ChatRequest(BaseModel):
    session_id: uuid.UUID
    message: str


class ChatResponse(BaseModel):
    session_id: uuid.UUID
    response: str
    agent: str = "agent_a"


@router.post("/chat", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> ChatResponse:
    """
    Send a message to Agent A (Partner A's private counselor).

    - Validates that the session belongs to this user and is a SOLO_A session.
    - Persists the human message (encrypted).
    - Invokes the Agent A LangGraph.
    - Persists the AI response (encrypted).
    - Returns the response.
    """
    # Verify session ownership and type
    result = await db.execute(
        select(Session).where(
            Session.id == body.session_id,
            Session.user_id == current_user.id,
            Session.session_type == SessionType.SOLO_A,
            Session.status == SessionStatus.ACTIVE,
        )
    )
    session = result.scalar_one_or_none()
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active SOLO_A session not found for this user.",
        )

    # Persist human message
    await save_message(
        db=db,
        session_id=body.session_id,
        role=MessageRole.HUMAN,
        content=body.message,
        user_key_encrypted=current_user.encrypted_key,
    )

    # Invoke Agent A
    try:
        response_text = await agent_a.chat(
            user_id=current_user.id,
            session_id=body.session_id,
            user_message=body.message,
            couple_id=session.couple_id,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent A error: {e}",
        )

    # Persist AI response
    await save_message(
        db=db,
        session_id=body.session_id,
        role=MessageRole.AI,
        content=response_text,
        user_key_encrypted=current_user.encrypted_key,
    )

    return ChatResponse(session_id=body.session_id, response=response_text)
