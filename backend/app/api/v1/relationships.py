"""Relationship management endpoints.

Handles creation of relationships and insight sync.
Also exposes the relational model read endpoint for Agent R context.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import text

from app.core.logging import get_logger
from app.deps import CurrentUser, DBSession
from app.privacy.mediator import PrivacyMediator
from app.privacy.schemas import SyncResult
from app.rkg import queries as rkg

router = APIRouter(prefix="/relationships", tags=["Relationships"])
logger = get_logger(__name__)


# ── Schemas ───────────────────────────────────────────────────────────────────


class CreateRelationshipRequest(BaseModel):
    partner_a_id: str
    partner_b_id: str
    partner_a_name: str | None = None
    partner_b_name: str | None = None


class CreateRelationshipResponse(BaseModel):
    relationship_id: str
    status: str = "active"


# ── Endpoints ─────────────────────────────────────────────────────────────────


@router.post("", response_model=CreateRelationshipResponse, status_code=status.HTTP_201_CREATED)
async def create_relationship(
    body: CreateRelationshipRequest,
    current_user: CurrentUser,
    db: DBSession,
) -> CreateRelationshipResponse:
    """Create a new relationship and initialize its RKG nodes.

    This seeds:
      - The relationships table in Postgres
      - Person nodes for both partners in Neo4j
      - The Relationship node in Neo4j linking both partners

    Called once during onboarding, after both partners have registered.
    """
    # Create DB record
    result = await db.execute(
        text(
            "INSERT INTO relationships (partner_a_id, partner_b_id, status) "
            "VALUES (:a_id, :b_id, 'active') "
            "RETURNING id"
        ),
        {"a_id": body.partner_a_id, "b_id": body.partner_b_id},
    )
    await db.commit()
    row = result.fetchone()
    if row is None:
        raise HTTPException(status_code=500, detail="Failed to create relationship record.")

    relationship_id = str(row[0])

    # Seed RKG
    try:
        await rkg.upsert_person(
            person_id=body.partner_a_id,
            partner_tag="partner_a",
        )
        await rkg.upsert_person(
            person_id=body.partner_b_id,
            partner_tag="partner_b",
        )
        await rkg.upsert_relationship(
            relationship_id=relationship_id,
            partner_a_id=body.partner_a_id,
            partner_b_id=body.partner_b_id,
        )
    except Exception as exc:
        logger.error("rkg_seed_failed", relationship_id=relationship_id, error=str(exc))
        # Don't fail the request — RKG can be reseeded; relationship record is the source of truth

    logger.info("relationship_created", relationship_id=relationship_id)
    return CreateRelationshipResponse(relationship_id=relationship_id)


@router.get("/{relationship_id}/model")
async def get_relational_model(
    relationship_id: str,
    current_user: CurrentUser,
) -> dict:
    """Return the current relational model for a relationship from the RKG.

    This is Agent R's primary context — active patterns, unmet needs,
    recent events, and therapy framework tags.

    Available to both partners in the relationship and to Agent R.
    No private content is ever included — only abstracted relational data.
    """
    if current_user.relationship_id != relationship_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this relationship.",
        )

    model = await rkg.get_relational_model(relationship_id)
    if not model:
        return {
            "relationship_id": relationship_id,
            "status": "no_data",
            "message": "No relational model data yet. Complete some sessions and run a sync first.",
        }
    return {"relationship_id": relationship_id, **model}


@router.post("/{relationship_id}/sync", response_model=SyncResult)
async def trigger_insight_sync(
    relationship_id: str,
    current_user: CurrentUser,
    db: DBSession,
) -> SyncResult:
    """Trigger an insight sync: process staged SAP signals and write to RKG.

    This picks up all unprocessed signals from sap_signals_staging for
    this relationship, aggregates them into relational patterns and needs,
    and upserts them into the Neo4j RKG.

    Call this:
      - After a series of solo sessions to update the relational model
      - Before a joint session to ensure Agent R has fresh context
      - On a schedule (e.g., daily background job)

    Only members of the relationship can trigger sync.
    """
    if current_user.relationship_id != relationship_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this relationship.",
        )

    mediator = PrivacyMediator(db=db)
    result = await mediator.trigger_sap_sync(relationship_id)

    logger.info(
        "insight_sync_triggered",
        relationship_id=relationship_id,
        signals_processed=result.signals_processed,
        patterns_upserted=result.patterns_upserted,
    )
    return result
