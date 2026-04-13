"""Neo4j Cypher query functions for the Relational Knowledge Graph.

All writes to the RKG come from the Privacy Mediator after SAP extraction.
Direct writes from agent nodes are prohibited — all data flowing into Neo4j
must be abstracted patterns, never raw private content.

Status: STUB — function signatures and docstrings are complete.
        Cypher implementations are marked with TODO.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.core.logging import get_logger
from app.rkg.neo4j_client import rkg_session

logger = get_logger(__name__)


# ── Person ────────────────────────────────────────────────────────────────────


async def upsert_person(
    person_id: str,
    partner_tag: str,
    attachment_style: str | None = None,
    emotional_vocabulary: list[str] | None = None,
    triggers: list[str] | None = None,
) -> None:
    """Create or update a Person node in the RKG.

    Args:
        person_id: UUID of the user (maps to the JWT sub claim).
        partner_tag: "partner_a" or "partner_b".
        attachment_style: e.g., "anxious", "avoidant", "secure", "disorganized".
        emotional_vocabulary: List of emotion words this person tends to use.
        triggers: Abstracted trigger themes (no raw quotes).
    """
    query = """
    MERGE (p:Person {id: $person_id})
    ON CREATE SET
        p.partner_tag          = $partner_tag,
        p.attachment_style     = $attachment_style,
        p.emotional_vocabulary = $emotional_vocabulary,
        p.triggers             = $triggers,
        p.created_at           = $now
    ON MATCH SET
        p.attachment_style     = COALESCE($attachment_style, p.attachment_style),
        p.emotional_vocabulary = COALESCE($emotional_vocabulary, p.emotional_vocabulary),
        p.triggers             = COALESCE($triggers, p.triggers),
        p.updated_at           = $now
    """
    async with rkg_session() as session:
        await session.run(
            query,
            person_id=person_id,
            partner_tag=partner_tag,
            attachment_style=attachment_style,
            emotional_vocabulary=emotional_vocabulary or [],
            triggers=triggers or [],
            now=datetime.now(UTC).isoformat(),
        )
    logger.debug("rkg_person_upserted", person_id=person_id)


# ── Relationship ──────────────────────────────────────────────────────────────


async def upsert_relationship(
    relationship_id: str,
    partner_a_id: str,
    partner_b_id: str,
    status: str = "active",
) -> None:
    """Create or update a Relationship node and link both partners.

    Creates the Relationship node and two PARTNER_IN edges if they don't exist.
    """
    query = """
    MERGE (r:Relationship {id: $relationship_id})
    ON CREATE SET
        r.partner_a_id = $partner_a_id,
        r.partner_b_id = $partner_b_id,
        r.status       = $status,
        r.health_score = 0.5,
        r.created_at   = $now
    ON MATCH SET
        r.status       = $status,
        r.updated_at   = $now
    WITH r
    MATCH (pa:Person {id: $partner_a_id})
    MERGE (pa)-[:PARTNER_IN]->(r)
    WITH r
    MATCH (pb:Person {id: $partner_b_id})
    MERGE (pb)-[:PARTNER_IN]->(r)
    """
    async with rkg_session() as session:
        await session.run(
            query,
            relationship_id=relationship_id,
            partner_a_id=partner_a_id,
            partner_b_id=partner_b_id,
            status=status,
            now=datetime.now(UTC).isoformat(),
        )
    logger.debug("rkg_relationship_upserted", relationship_id=relationship_id)


# ── RelationalPattern ─────────────────────────────────────────────────────────


async def upsert_pattern(
    relationship_id: str,
    pattern_id: str,
    name: str,
    category: str,
    intensity: float,
    insight_tags: list[str] | None = None,
) -> None:
    """Create or update a RelationalPattern node and link it to a Relationship.

    Also creates TAGGED_WITH edges to any TherapyFrameInsight nodes specified.

    Args:
        relationship_id: The relationship this pattern belongs to.
        pattern_id: Stable identifier for this pattern (e.g., "pursue_withdraw_primary").
        name: Human-readable pattern name.
        category: Broad category (e.g., "conflict_cycle", "connection_deficit", "repair").
        intensity: 0.0–1.0 intensity score from SAP extraction.
        insight_tags: List of TherapyFrameInsight IDs to tag this pattern with.
    """
    query = """
    MATCH (r:Relationship {id: $relationship_id})
    MERGE (rp:RelationalPattern {id: $pattern_id})
    ON CREATE SET
        rp.name          = $name,
        rp.category      = $category,
        rp.intensity     = $intensity,
        rp.last_observed = $now,
        rp.created_at    = $now
    ON MATCH SET
        rp.intensity     = $intensity,
        rp.last_observed = $now
    MERGE (r)-[:HAS_PATTERN]->(rp)
    """
    async with rkg_session() as session:
        await session.run(
            query,
            relationship_id=relationship_id,
            pattern_id=pattern_id,
            name=name,
            category=category,
            intensity=intensity,
            now=datetime.now(UTC).isoformat(),
        )
        if insight_tags:
            tag_query = """
            MATCH (rp:RelationalPattern {id: $pattern_id})
            UNWIND $tags AS tag_id
            MATCH (t:TherapyFrameInsight {id: tag_id})
            MERGE (rp)-[:TAGGED_WITH]->(t)
            """
            await session.run(tag_query, pattern_id=pattern_id, tags=insight_tags)

    logger.debug("rkg_pattern_upserted", pattern_id=pattern_id, intensity=intensity)


# ── NeedCluster ───────────────────────────────────────────────────────────────


async def upsert_need_cluster(
    pattern_id: str,
    need_id: str,
    theme: str,
    priority: float,
    partner_tag: str,
) -> None:
    """Create or update a NeedCluster and link it to a RelationalPattern.

    Args:
        pattern_id: The RelationalPattern this need is surfaced from.
        need_id: Stable identifier.
        theme: Abstracted need theme (e.g., "felt_security", "autonomy", "recognition").
        priority: 0.0–1.0 urgency score.
        partner_tag: Which partner's need this is (used by Agent R for empathy bridging).
    """
    query = """
    MATCH (rp:RelationalPattern {id: $pattern_id})
    MERGE (n:NeedCluster {id: $need_id})
    ON CREATE SET
        n.theme       = $theme,
        n.priority    = $priority,
        n.partner_tag = $partner_tag,
        n.created_at  = $now
    ON MATCH SET
        n.priority    = $priority,
        n.updated_at  = $now
    MERGE (rp)-[:INVOLVES_NEED]->(n)
    """
    async with rkg_session() as session:
        await session.run(
            query,
            pattern_id=pattern_id,
            need_id=need_id,
            theme=theme,
            priority=priority,
            partner_tag=partner_tag,
            now=datetime.now(UTC).isoformat(),
        )


# ── Event ─────────────────────────────────────────────────────────────────────


async def record_event(
    relationship_id: str,
    event_id: str,
    event_type: str,
    resolved: bool = False,
    insight_tags: list[str] | None = None,
) -> None:
    """Record a relational event (conflict, repair, breakthrough).

    Args:
        relationship_id: The relationship this event belongs to.
        event_id: Unique event ID.
        event_type: "conflict" | "repair" | "breakthrough" | "check_in".
        resolved: Whether the event has been resolved/processed.
        insight_tags: TherapyFrameInsight IDs to tag this event with.
    """
    query = """
    MATCH (r:Relationship {id: $relationship_id})
    MERGE (e:Event {id: $event_id})
    ON CREATE SET
        e.type       = $event_type,
        e.resolved   = $resolved,
        e.timestamp  = $now,
        e.created_at = $now
    ON MATCH SET
        e.resolved   = $resolved,
        e.updated_at = $now
    MERGE (r)-[:HAS_EVENT]->(e)
    """
    async with rkg_session() as session:
        await session.run(
            query,
            relationship_id=relationship_id,
            event_id=event_id,
            event_type=event_type,
            resolved=resolved,
            now=datetime.now(UTC).isoformat(),
        )
        if insight_tags:
            tag_query = """
            MATCH (e:Event {id: $event_id})
            UNWIND $tags AS tag_id
            MATCH (t:TherapyFrameInsight {id: tag_id})
            MERGE (e)-[:TAGGED_WITH]->(t)
            """
            await session.run(tag_query, event_id=event_id, tags=insight_tags)


# ── Reads ─────────────────────────────────────────────────────────────────────


async def get_relational_model(relationship_id: str) -> dict[str, Any]:
    """Fetch the current relational model for Agent R's context.

    Returns a summary dict containing:
    - active patterns (sorted by intensity desc)
    - unmet needs for each partner
    - recent events (last 10, unresolved first)
    - tagged therapy framework insights

    This is the only read path for the RKG — Agent R calls this before
    every response to ground its understanding in the current dynamic.
    """
    query = """
    MATCH (r:Relationship {id: $relationship_id})
    OPTIONAL MATCH (r)-[:HAS_PATTERN]->(rp:RelationalPattern)
    OPTIONAL MATCH (rp)-[:INVOLVES_NEED]->(n:NeedCluster)
    OPTIONAL MATCH (rp)-[:TAGGED_WITH]->(ti:TherapyFrameInsight)
    OPTIONAL MATCH (r)-[:HAS_EVENT]->(e:Event)
    RETURN
        r,
        collect(DISTINCT {
            id: rp.id, name: rp.name, category: rp.category,
            intensity: rp.intensity, last_observed: rp.last_observed
        }) AS patterns,
        collect(DISTINCT {
            id: n.id, theme: n.theme, priority: n.priority, partner_tag: n.partner_tag
        }) AS needs,
        collect(DISTINCT {
            id: ti.id, framework: ti.framework, tag: ti.tag
        }) AS insights,
        collect(DISTINCT {
            id: e.id, type: e.type, resolved: e.resolved, timestamp: e.timestamp
        }) AS events
    """
    async with rkg_session() as session:
        result = await session.run(query, relationship_id=relationship_id)
        record = await result.single()
        if record is None:
            return {}

        return {
            "relationship": dict(record["r"]),
            "active_patterns": sorted(
                [p for p in record["patterns"] if p["id"] is not None],
                key=lambda x: x.get("intensity", 0),
                reverse=True,
            ),
            "unmet_needs": [n for n in record["needs"] if n["id"] is not None],
            "insights": [i for i in record["insights"] if i["id"] is not None],
            "recent_events": sorted(
                [e for e in record["events"] if e["id"] is not None],
                key=lambda x: x.get("timestamp", ""),
                reverse=True,
            )[:10],
        }
