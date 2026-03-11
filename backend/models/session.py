"""
Session ORM models.

A Session tracks one interaction context — solo (A or B) or joint.
Sessions gate Insight Sync: when a solo session closes, the Privacy Mediator
synthesises patterns and updates the RKG.
"""
import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.postgres import Base


class SessionType(str, Enum):
    SOLO_A = "solo_a"       # Partner A + Agent A (private)
    SOLO_B = "solo_b"       # Partner B + Agent B (private)
    JOINT = "joint"         # Both partners + Agent R (mediated)


class SessionStatus(str, Enum):
    ACTIVE = "active"
    CLOSED = "closed"       # Triggers Insight Sync for solo sessions


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    # For joint sessions, couple_id is set; user_id is the initiating partner.
    couple_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("couples.id"), nullable=True, index=True
    )
    session_type: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default=SessionStatus.ACTIVE, nullable=False)

    # LangGraph thread_id used as the checkpoint key
    thread_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Whether insight sync has been run for this session
    insight_synced: Mapped[bool] = mapped_column(default=False)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="sessions")  # type: ignore[name-defined]  # noqa: F821
    messages: Mapped[list["Message"]] = relationship(back_populates="session")  # type: ignore[name-defined]  # noqa: F821

    def __repr__(self) -> str:
        return f"<Session id={self.id} type={self.session_type} status={self.status}>"
