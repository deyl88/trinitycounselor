"""
Pattern model — abstracted relational patterns synthesised by the Privacy Mediator.

These records are the *bridge* between private conversation stores and the RKG.
They contain no raw content, only LLM-synthesised abstractions safe to share
with the Relationship Agent.
"""
import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.db.postgres import Base


class PatternType(str, Enum):
    ATTACHMENT = "attachment"           # Attachment style signals
    EMOTIONAL = "emotional"             # Emotional pattern / regulation style
    COMMUNICATION = "communication"     # Communication dynamics
    NEED = "need"                       # Unmet need cluster
    CONFLICT = "conflict"               # Conflict pattern (pursue/withdraw, etc.)
    REPAIR = "repair"                   # Repair attempt signal
    BREAKTHROUGH = "breakthrough"       # Positive relational event
    TRIGGER = "trigger"                 # Identified trigger pattern


class AbstractedPattern(Base):
    """
    A single synthesised pattern abstracted from a solo session.
    Written to postgres by the Privacy Mediator, then mirrored to Neo4j RKG.

    PRIVACY CONTRACT: content field must NEVER contain direct quotes,
    names, or identifiable details from the raw conversation.
    """
    __tablename__ = "abstracted_patterns"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sessions.id"), nullable=False, index=True
    )
    pattern_type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)

    # Plain-text abstraction — e.g. "expresses fear of abandonment when partner withdraws"
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Therapy framework tag (EFT, Gottman, IFS, Attachment, Esther_Perel, FamilySystems)
    framework_tag: Mapped[str | None] = mapped_column(String(30), nullable=True)

    # Whether this pattern has been written to the Neo4j RKG
    rkg_synced: Mapped[bool] = mapped_column(default=False)
    rkg_node_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Confidence score from synthesiser (0.0–1.0)
    confidence: Mapped[float] = mapped_column(default=1.0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self) -> str:
        return f"<AbstractedPattern id={self.id} type={self.pattern_type}>"
