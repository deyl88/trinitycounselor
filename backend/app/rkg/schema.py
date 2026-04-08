"""Neo4j RKG schema initialization.

Idempotent — safe to run on every startup. Uses IF NOT EXISTS guards
on all constraints and indexes.

Node types
──────────
  Person             — attachment profile for each partner
  Relationship       — the couple (the primary client)
  RelationalPattern  — recurring dynamics (e.g., withdraw-pursue)
  NeedCluster        — unmet attachment needs
  Event              — conflict, repair, breakthrough moments
  TherapyFrameInsight — tagged insights from EFT/Gottman/IFS/Attachment

Relationship types
──────────────────
  PARTNER_IN      (:Person)     → (:Relationship)
  HAS_PATTERN     (:Relationship) → (:RelationalPattern)
  INVOLVES_NEED   (:RelationalPattern) → (:NeedCluster)
  HAS_EVENT       (:Relationship) → (:Event)
  TAGGED_WITH     (:Event | :RelationalPattern) → (:TherapyFrameInsight)
"""

from app.core.logging import get_logger
from app.rkg.neo4j_client import rkg_session

logger = get_logger(__name__)

# ── Constraints (enforce uniqueness + create implicit index) ──────────────────
_CONSTRAINTS = [
    "CREATE CONSTRAINT person_id IF NOT EXISTS FOR (p:Person) REQUIRE p.id IS UNIQUE",
    "CREATE CONSTRAINT relationship_id IF NOT EXISTS FOR (r:Relationship) REQUIRE r.id IS UNIQUE",
    "CREATE CONSTRAINT pattern_id IF NOT EXISTS FOR (rp:RelationalPattern) REQUIRE rp.id IS UNIQUE",
    "CREATE CONSTRAINT need_id IF NOT EXISTS FOR (n:NeedCluster) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT event_id IF NOT EXISTS FOR (e:Event) REQUIRE e.id IS UNIQUE",
    "CREATE CONSTRAINT insight_id IF NOT EXISTS FOR (t:TherapyFrameInsight) REQUIRE t.id IS UNIQUE",
]

# ── Indexes (additional lookup patterns) ─────────────────────────────────────
_INDEXES = [
    "CREATE INDEX person_attachment IF NOT EXISTS FOR (p:Person) ON (p.attachment_style)",
    "CREATE INDEX pattern_category IF NOT EXISTS FOR (rp:RelationalPattern) ON (rp.category)",
    "CREATE INDEX pattern_intensity IF NOT EXISTS FOR (rp:RelationalPattern) ON (rp.intensity)",
    "CREATE INDEX event_type IF NOT EXISTS FOR (e:Event) ON (e.type)",
    "CREATE INDEX event_timestamp IF NOT EXISTS FOR (e:Event) ON (e.timestamp)",
    "CREATE INDEX insight_framework IF NOT EXISTS FOR (t:TherapyFrameInsight) ON (t.framework)",
    "CREATE INDEX relationship_status IF NOT EXISTS FOR (r:Relationship) ON (r.status)",
]

# ── Seed data: canonical TherapyFrameInsight nodes ───────────────────────────
# These are reused across all relationships via TAGGED_WITH edges.
_SEED_INSIGHTS = [
    # EFT
    {"id": "eft:attachment_injury", "framework": "EFT", "tag": "attachment_injury",
     "description": "A key moment where one partner felt abandoned or betrayed."},
    {"id": "eft:pursue_withdraw", "framework": "EFT", "tag": "pursue_withdraw",
     "description": "Classic EFT dance: one partner pursues, the other withdraws."},
    {"id": "eft:emotional_accessibility", "framework": "EFT", "tag": "emotional_accessibility",
     "description": "Ability to be emotionally present and reachable for a partner."},
    # Gottman
    {"id": "gottman:criticism", "framework": "Gottman", "tag": "criticism",
     "description": "Attacking the partner's character rather than specific behavior."},
    {"id": "gottman:contempt", "framework": "Gottman", "tag": "contempt",
     "description": "Eye-rolling, sarcasm, mockery — the strongest predictor of divorce."},
    {"id": "gottman:defensiveness", "framework": "Gottman", "tag": "defensiveness",
     "description": "Counter-attack or innocent victim stance to deflect criticism."},
    {"id": "gottman:stonewalling", "framework": "Gottman", "tag": "stonewalling",
     "description": "Emotional shutdown and withdrawal from interaction."},
    {"id": "gottman:repair_attempt", "framework": "Gottman", "tag": "repair_attempt",
     "description": "Any action attempting to de-escalate negativity during conflict."},
    # IFS
    {"id": "ifs:protector_activated", "framework": "IFS", "tag": "protector_activated",
     "description": "A protective inner part taking over to prevent vulnerability."},
    {"id": "ifs:exile_triggered", "framework": "IFS", "tag": "exile_triggered",
     "description": "Wounded exile part activated, driving intense emotional reaction."},
    # Attachment
    {"id": "attachment:anxious", "framework": "Attachment", "tag": "anxious_style",
     "description": "Anxious attachment pattern: hyperactivation of attachment system."},
    {"id": "attachment:avoidant", "framework": "Attachment", "tag": "avoidant_style",
     "description": "Avoidant attachment pattern: deactivation of attachment system."},
    {"id": "attachment:secure", "framework": "Attachment", "tag": "secure_base",
     "description": "Moment of secure functioning — felt safety with the partner."},
]

_SEED_INSIGHT_QUERY = """
UNWIND $insights AS insight
MERGE (t:TherapyFrameInsight {id: insight.id})
ON CREATE SET
    t.framework   = insight.framework,
    t.tag         = insight.tag,
    t.description = insight.description
"""


async def init_schema() -> None:
    """Run all DDL statements to initialize the RKG schema.

    Idempotent — IF NOT EXISTS guards prevent duplicate errors.
    Called once during application startup via the lifespan handler.
    """
    async with rkg_session() as session:
        for stmt in _CONSTRAINTS:
            await session.run(stmt)
        for stmt in _INDEXES:
            await session.run(stmt)
        await session.run(_SEED_INSIGHT_QUERY, insights=_SEED_INSIGHTS)

    logger.info(
        "rkg_schema_initialized",
        constraints=len(_CONSTRAINTS),
        indexes=len(_INDEXES),
        seed_insights=len(_SEED_INSIGHTS),
    )
