"""
Session lifecycle management routes.

Endpoints:
  POST /sessions/                — create a new session
  POST /sessions/{id}/close      — close a session (triggers Insight Sync for solo)
  GET  /sessions/{id}            — get session metadata
  GET  /sessions/                — list user's sessions

  POST /sessions/invite          — create a couple invite code
  POST /sessions/invite/accept   — accept a couple invite

  POST /auth/register            — register a new user
  POST /auth/login               — get a JWT token
"""
import secrets
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.middleware.auth import get_current_user
from backend.auth.jwt import TokenPair, create_access_token
from backend.auth.keys import encrypt_user_key, generate_user_key
from backend.db.postgres import get_session
from backend.db.neo4j import get_driver
from backend.graph.rkg_client import RKGClient
from backend.models.session import Session, SessionStatus, SessionType
from backend.models.user import Couple, CoupleInvite, User
from backend.privacy.mediator import PrivacyMediator

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ─────────────────────────────────────────────────────────────────────────────
# Auth
# ─────────────────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    display_name: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/auth/register", response_model=TokenPair, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_session)) -> TokenPair:
    """Register a new user. Returns a JWT access token."""
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered.")

    user_key = generate_user_key()
    encrypted_key = encrypt_user_key(user_key)

    user = User(
        email=body.email,
        hashed_password=pwd_context.hash(body.password),
        display_name=body.display_name,
        encrypted_key=encrypted_key,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    # Create the Person node in the RKG
    rkg = RKGClient()
    await rkg.upsert_person(user_id=user.id)

    token = create_access_token(user.id, user.email)
    return TokenPair(access_token=token)


@router.post("/auth/login", response_model=TokenPair)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_session)) -> TokenPair:
    """Authenticate and return a JWT access token."""
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if user is None or not pwd_context.verify(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    token = create_access_token(user.id, user.email)
    return TokenPair(access_token=token)


# ─────────────────────────────────────────────────────────────────────────────
# Session lifecycle
# ─────────────────────────────────────────────────────────────────────────────

class CreateSessionRequest(BaseModel):
    session_type: SessionType


class SessionResponse(BaseModel):
    id: uuid.UUID
    session_type: str
    status: str
    thread_id: str
    started_at: datetime
    couple_id: uuid.UUID | None


@router.post("/", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    body: CreateSessionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> SessionResponse:
    """Create a new session for the authenticated user."""
    session_id = uuid.uuid4()
    thread_id = f"{current_user.id}:{session_id}"

    # Resolve couple_id for joint sessions
    couple_id = None
    if body.session_type == SessionType.JOINT:
        result = await db.execute(
            select(Couple).where(
                Couple.active == True,  # noqa: E712
                (Couple.partner_a_id == current_user.id) | (Couple.partner_b_id == current_user.id),
            )
        )
        couple = result.scalar_one_or_none()
        if couple is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You must be part of an active couple to create a joint session.",
            )
        couple_id = couple.id
        thread_id = f"r:{session_id}"  # Agent R thread scoped to session, not user

    session = Session(
        id=session_id,
        user_id=current_user.id,
        couple_id=couple_id,
        session_type=body.session_type.value,
        status=SessionStatus.ACTIVE.value,
        thread_id=thread_id,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    return SessionResponse(
        id=session.id,
        session_type=session.session_type,
        status=session.status,
        thread_id=session.thread_id,
        started_at=session.started_at,
        couple_id=session.couple_id,
    )


@router.post("/{session_id}/close", response_model=dict)
async def close_session(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> dict:
    """
    Close a session.

    For SOLO_A and SOLO_B sessions: triggers the Insight Sync pipeline
    (pattern synthesis → RKG write). This is the privacy boundary event.

    Returns the number of patterns extracted.
    """
    result = await db.execute(
        select(Session).where(
            Session.id == session_id,
            Session.user_id == current_user.id,
            Session.status == SessionStatus.ACTIVE,
        )
    )
    session = result.scalar_one_or_none()
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Active session not found.")

    # Mark session closed
    session.status = SessionStatus.CLOSED.value
    session.closed_at = datetime.now(UTC)
    await db.commit()

    # Trigger Insight Sync for solo sessions
    patterns_extracted = 0
    if session.session_type in (SessionType.SOLO_A.value, SessionType.SOLO_B.value):
        try:
            rkg = RKGClient()
            mediator = PrivacyMediator(db=db, rkg=rkg)
            patterns_extracted = await mediator.run_insight_sync(session_id)
        except Exception:  # noqa: BLE001
            # Insight Sync failure does not prevent session closure
            pass

    return {
        "session_id": str(session_id),
        "status": "closed",
        "patterns_extracted": patterns_extracted,
    }


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session_detail(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> SessionResponse:
    result = await db.execute(
        select(Session).where(
            Session.id == session_id,
            Session.user_id == current_user.id,
        )
    )
    session = result.scalar_one_or_none()
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")

    return SessionResponse(
        id=session.id,
        session_type=session.session_type,
        status=session.status,
        thread_id=session.thread_id,
        started_at=session.started_at,
        couple_id=session.couple_id,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Couple invite flow
# ─────────────────────────────────────────────────────────────────────────────

class InviteResponse(BaseModel):
    invite_code: str
    expires_at: datetime


class AcceptInviteRequest(BaseModel):
    invite_code: str


@router.post("/invite", response_model=InviteResponse, status_code=status.HTTP_201_CREATED)
async def create_invite(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> InviteResponse:
    """Create a couple invite code. Partner A sends this to Partner B out-of-band."""
    # Check not already in an active couple
    result = await db.execute(
        select(Couple).where(
            Couple.active == True,  # noqa: E712
            (Couple.partner_a_id == current_user.id) | (Couple.partner_b_id == current_user.id),
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You are already part of an active couple.",
        )

    invite_code = secrets.token_urlsafe(32)
    expires_at = datetime.now(UTC) + timedelta(days=7)

    invite = CoupleInvite(
        inviter_id=current_user.id,
        invite_code=invite_code,
        expires_at=expires_at,
    )
    db.add(invite)
    await db.commit()

    return InviteResponse(invite_code=invite_code, expires_at=expires_at)


@router.post("/invite/accept", response_model=dict, status_code=status.HTTP_201_CREATED)
async def accept_invite(
    body: AcceptInviteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> dict:
    """Accept a couple invite. Creates the Couple record and links both partners."""
    result = await db.execute(
        select(CoupleInvite).where(
            CoupleInvite.invite_code == body.invite_code,
            CoupleInvite.accepted == False,  # noqa: E712
            CoupleInvite.expires_at > datetime.now(UTC),
        )
    )
    invite = result.scalar_one_or_none()
    if invite is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid, expired, or already-used invite code.",
        )

    if invite.inviter_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot accept your own invite.",
        )

    couple = Couple(
        partner_a_id=invite.inviter_id,
        partner_b_id=current_user.id,
    )
    db.add(couple)

    invite.accepted = True
    await db.commit()
    await db.refresh(couple)

    # Create/link the Couple node in the RKG
    rkg = RKGClient()
    await rkg.upsert_couple(
        couple_id=couple.id,
        partner_a_id=invite.inviter_id,
        partner_b_id=current_user.id,
    )

    return {"couple_id": str(couple.id), "status": "couple_created"}
