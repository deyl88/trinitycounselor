"""
Message ORM model — stores individual chat turns within a session.

Raw message content is encrypted at rest using the owning user's key.
The LangGraph checkpointer also stores conversation state in postgres,
but this model provides an auditable, queryable history per session.
"""
import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, LargeBinary, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.postgres import Base


class MessageRole(str, Enum):
    HUMAN = "human"
    AI = "ai"
    SYSTEM = "system"


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sessions.id"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)

    # Content is stored encrypted (AES-256-GCM) with the user's per-user key.
    # Encrypted as: nonce (12 bytes) || ciphertext, then hex-encoded.
    content_encrypted: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)

    token_count: Mapped[int | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    session: Mapped["Session"] = relationship(back_populates="messages")  # type: ignore[name-defined]  # noqa: F821

    def __repr__(self) -> str:
        return f"<Message id={self.id} role={self.role} session={self.session_id}>"
