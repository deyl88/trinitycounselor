"""Pydantic schemas for Privacy Mediator and SAP data structures."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

# ── SAP Signal ────────────────────────────────────────────────────────────────


class SAPSignal(BaseModel):
    """A single abstracted signal extracted by the Signal Abstraction Protocol.

    This is the fundamental unit of information that crosses the privacy
    boundary from a private agent into the Relational Knowledge Graph.

    Invariant: A SAPSignal must contain NO quotes, NO names, NO identifying
    details. Only categorical patterns and intensities.
    """

    signal_type: Literal[
        "emotional_state",
        "attachment_need",
        "conflict_dynamic",
        "connection_moment",
        "crisis_indicator",
        "therapeutic_progress",
    ] = Field(description="Category of the signal.")

    themes: list[str] = Field(
        min_length=1,
        max_length=5,
        description=(
            "Categorical theme labels. Snake_case. No quotes, no names, no specifics. "
            "Examples: 'feeling_unheard', 'emotional_exhaustion', 'pursue_withdraw'."
        ),
    )

    intensity: float = Field(
        ge=0.0,
        le=1.0,
        description="Signal strength: 0.0 = minimal, 0.5 = moderate, 1.0 = dominant/urgent.",
    )

    category: str = Field(
        description=(
            "Broad relational category. "
            "Examples: 'connection_deficit', 'conflict_cycle', 'repair', 'safety_concern'."
        )
    )

    valence: Literal["positive", "negative", "mixed"] = Field(
        description="Emotional valence of the signal."
    )

    source_tag: Literal["partner_a", "partner_b"] = Field(
        description="Which partner this signal was extracted from."
    )

    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="When this signal was extracted.",
    )

    @field_validator("themes")
    @classmethod
    def themes_must_be_categorical(cls, v: list[str]) -> list[str]:
        for theme in v:
            if len(theme.split()) > 4:
                raise ValueError(
                    f"Theme '{theme}' appears too specific — themes should be short categorical labels."
                )
        return v


# ── SAP Extraction Result ─────────────────────────────────────────────────────


class SAPExtractionResult(BaseModel):
    """Result of a single SAP extraction call."""

    signals: list[SAPSignal]
    source_agent: str
    relationship_id: str
    extracted_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @property
    def has_crisis_indicator(self) -> bool:
        return any(s.signal_type == "crisis_indicator" for s in self.signals)

    @property
    def dominant_signal(self) -> SAPSignal | None:
        if not self.signals:
            return None
        return max(self.signals, key=lambda s: s.intensity)


# ── Sync Result ───────────────────────────────────────────────────────────────


class SyncResult(BaseModel):
    """Result of a Privacy Mediator insight sync operation."""

    relationship_id: str
    signals_processed: int
    patterns_upserted: int
    needs_upserted: int
    events_recorded: int
    synced_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    errors: list[str] = Field(default_factory=list)

    @property
    def success(self) -> bool:
        return len(self.errors) == 0
