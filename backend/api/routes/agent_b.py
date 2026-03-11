"""
Agent B API routes — Private Counselor for Partner B.

Mirror of agent_a.py routes. Session type enforced as SOLO_B.
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.agents import agent_b
from backend.api.middleware.auth import get_current_user
from backend.db.postgres import get_session
from backend.memory.conversation_store import save_message
from backend.models.message import MessageRole
from backend.models.session import Session, SessionStatus, SessionType
from backend.models.user import User

router = APIRouter()


class ChatRequest(BaseModel):
    session_id: uuid.UUID
    message: str


class ChatResponse(BaseModel):
    session_id: uuid.UUID
    response: str
    agent: str = "agent_b"


@router.post("/chat", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> ChatResponse:
    """Send a message to Agent B (Partner B's private counselor)."""
    result = await db.execute(
        select(Session).where(
            Session.id == body.session_id,
            Session.user_id == current_user.id,
            Session.session_type == SessionType.SOLO_B,
            Session.status == SessionStatus.ACTIVE,
        )
    )
    session = result.scalar_one_or_none()
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active SOLO_B session not found for this user.",
        )

    await save_message(
        db=db,
        session_id=body.session_id,
        role=MessageRole.HUMAN,
        content=body.message,
        user_key_encrypted=current_user.encrypted_key,
    )

    try:
        response_text = await agent_b.chat(
            user_id=current_user.id,
            session_id=body.session_id,
            user_message=body.message,
            couple_id=session.couple_id,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent B error: {e}",
        )

    await save_message(
        db=db,
        session_id=body.session_id,
        role=MessageRole.AI,
        content=response_text,
        user_key_encrypted=current_user.encrypted_key,
    )

    return ChatResponse(session_id=body.session_id, response=response_text)
