"""
Relational Knowledge Graph (RKG) client.

Wraps the Neo4j async driver with typed methods for all RKG operations.
Only accepts abstracted data — never raw conversation content.
"""
import uuid

from neo4j import AsyncDriver

from backend.db.neo4j import get_driver
from backend.graph import queries
from backend.models.pattern import AbstractedPattern


class RKGClient:
    """
    High-level interface to the Neo4j RKG.
    Instantiate per-request (stateless — driver is shared globally).
    """

    def __init__(self, driver: AsyncDriver | None = None) -> None:
        self._driver = driver or get_driver()

    # ─────────────────────────────────────────────────────────────────────────
    # Person
    # ─────────────────────────────────────────────────────────────────────────

    async def upsert_person(
        self,
        user_id: uuid.UUID,
        couple_id: uuid.UUID | None = None,
        attachment_style: str = "unknown",
        emotional_vocabulary_level: str = "medium",
        regulation_style: str = "unknown",
    ) -> None:
        async with self._driver.session() as session:
            await session.run(
                queries.UPSERT_PERSON,
                user_id=str(user_id),
                couple_id=str(couple_id) if couple_id else None,
                attachment_style=attachment_style,
                emotional_vocabulary_level=emotional_vocabulary_level,
                regulation_style=regulation_style,
            )

    async def get_person_patterns(
        self, user_id: uuid.UUID, limit: int = 10
    ) -> list[dict]:
        async with self._driver.session() as session:
            result = await session.run(
                queries.GET_PERSON_PATTERNS,
                user_id=str(user_id),
                limit=limit,
            )
            return [dict(r["rp"]) async for r in result]

    # ─────────────────────────────────────────────────────────────────────────
    # Couple
    # ─────────────────────────────────────────────────────────────────────────

    async def upsert_couple(
        self,
        couple_id: uuid.UUID,
        partner_a_id: uuid.UUID,
        partner_b_id: uuid.UUID,
        primary_cycle: str = "unknown",
        eft_stage: str = "de-escalation",
    ) -> None:
        async with self._driver.session() as session:
            await session.run(
                queries.UPSERT_COUPLE,
                couple_id=str(couple_id),
                partner_a_id=str(partner_a_id),
                partner_b_id=str(partner_b_id),
                primary_cycle=primary_cycle,
                eft_stage=eft_stage,
            )

    async def get_relationship_summary(self, couple_id: uuid.UUID) -> dict:
        """
        Retrieve the full relational context for a couple.
        Used by Agent R to build its system prompt context.
        """
        async with self._driver.session() as session:
            result = await session.run(
                queries.GET_RELATIONSHIP_SUMMARY,
                couple_id=str(couple_id),
            )
            record = await result.single()
            if record is None:
                return {"patterns": [], "events": [], "partners": []}
            return dict(record)

    # ─────────────────────────────────────────────────────────────────────────
    # Patterns
    # ─────────────────────────────────────────────────────────────────────────

    async def upsert_pattern(
        self,
        user_id: uuid.UUID,
        couple_id: uuid.UUID | None,
        pattern: AbstractedPattern,
    ) -> str:
        """
        Write an AbstractedPattern to the RKG.
        Returns the neo4j pattern_id (same as pattern.id).
        """
        pattern_id = str(pattern.id)
        async with self._driver.session() as session:
            # Write the pattern and link to the Person
            await session.run(
                queries.UPSERT_RELATIONAL_PATTERN,
                pattern_id=pattern_id,
                user_id=str(user_id),
                pattern_type=pattern.pattern_type,
                description=pattern.content,
                framework_tag=pattern.framework_tag,
                confidence=pattern.confidence,
            )

            # Also link to Couple if this is a couple session
            if couple_id is not None:
                await session.run(
                    queries.LINK_PATTERN_TO_COUPLE,
                    pattern_id=pattern_id,
                    couple_id=str(couple_id),
                )

        return pattern_id

    async def create_event(
        self,
        couple_id: uuid.UUID,
        event_type: str,
        theme: str,
        resolution_signal: str = "unresolved",
    ) -> str:
        event_id = str(uuid.uuid4())
        async with self._driver.session() as session:
            await session.run(
                queries.CREATE_EVENT,
                event_id=event_id,
                couple_id=str(couple_id),
                event_type=event_type,
                theme=theme,
                resolution_signal=resolution_signal,
            )
        return event_id
