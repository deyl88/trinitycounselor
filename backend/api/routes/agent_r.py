"""
Agent R API routes — Relationship Agent (Mediator / Third Presence).

Endpoints:
  POST /agent-r/chat    — message Agent R directly (solo relational overview)
  POST /agent-r/joint   — joint session message (both partners context)

Agent R loads context from the RKG, never from either partner's private store.
Both partners in a couple can access Agent R; they are identified by their
couple membership and the session type (JOINT).
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.agents import agent_r
from backend.api.middleware.auth import get_current_user
from backend.db.postgres import get_session
from backend.models.session import Session, SessionStatus, SessionType
from backend.models.user import Couple, User

router = APIRouter()


class ChatRequest(BaseModel):
    session_id: uuid.UUID
    message: str


class ChatResponse(BaseModel):
    session_id: uuid.UUID
    response: str
    agent: str = "agent_r"


async def _get_couple_for_user(db: AsyncSession, user_id: uuid.UUID) -> Couple | None:
    """Find the active couple this user belongs to (as either partner)."""
    result = await db.execute(
        select(Couple).where(
            Couple.active == True,  # noqa: E712
            (Couple.partner_a_id == user_id) | (Couple.partner_b_id == user_id),
        )
    )
    return result.scalar_one_or_none()


@router.post("/chat", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> ChatResponse:
    """
    Send a message to Agent R for a relational overview (solo interaction).

    The user must be part of a couple. Agent R will use RKG data to provide
    a systemic perspective on the relationship — without revealing the
    partner's private content.
    """
    couple = await _get_couple_for_user(db, current_user.id)
    if couple is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be part of an active couple to access Agent R.",
        )

    # Verify session
    result = await db.execute(
        select(Session).where(
            Session.id == body.session_id,
            Session.status == SessionStatus.ACTIVE,
        )
    )
    session = result.scalar_one_or_none()
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active session not found.",
        )

    try:
        response_text = await agent_r.chat(
            user_id=current_user.id,
            session_id=body.session_id,
            user_message=body.message,
            couple_id=couple.id,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent R error: {e}",
        )

    return ChatResponse(session_id=body.session_id, response=response_text)


@router.post("/joint", response_model=ChatResponse)
async def joint_session(
    body: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> ChatResponse:
    """
    Send a message in a joint session (both partners present, Agent R mediating).

    Session must be of type JOINT. Either partner can send messages.
    Agent R maintains the joint session thread via the session_id.
    """
    couple = await _get_couple_for_user(db, current_user.id)
    if couple is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be part of an active couple to access a joint session.",
        )

    result = await db.execute(
        select(Session).where(
            Session.id == body.session_id,
            Session.session_type == SessionType.JOINT,
            Session.status == SessionStatus.ACTIVE,
            Session.couple_id == couple.id,
        )
    )
    session = result.scalar_one_or_none()
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active JOINT session not found for this couple.",
        )

    try:
        response_text = await agent_r.chat(
            user_id=current_user.id,
            session_id=body.session_id,
            user_message=body.message,
            couple_id=couple.id,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent R error: {e}",
        )

    return ChatResponse(session_id=body.session_id, response=response_text)
