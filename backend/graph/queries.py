"""
Typed Cypher query library for the Relational Knowledge Graph (RKG).

All write operations go through this module to enforce the privacy contract:
only abstracted patterns and relational signals may enter the graph.
"""
import uuid
from dataclasses import dataclass
from enum import Enum


class AttachmentStyle(str, Enum):
    ANXIOUS = "anxious"
    AVOIDANT = "avoidant"
    SECURE = "secure"
    DISORGANISED = "disorganised"
    UNKNOWN = "unknown"


class RelationshipStage(str, Enum):
    FORMING = "forming"
    STORMING = "storming"
    NORMING = "norming"
    PERFORMING = "performing"


@dataclass
class PersonProfile:
    user_id: uuid.UUID
    couple_id: uuid.UUID | None
    attachment_style: str = AttachmentStyle.UNKNOWN
    emotional_vocabulary_level: str = "medium"
    regulation_style: str = "unknown"


# ─────────────────────────────────────────────────────────────────────────────
# Person queries
# ─────────────────────────────────────────────────────────────────────────────

UPSERT_PERSON = """
MERGE (p:Person {user_id: $user_id})
SET p.couple_id          = $couple_id,
    p.attachment_style   = $attachment_style,
    p.emotional_vocabulary_level = $emotional_vocabulary_level,
    p.regulation_style   = $regulation_style,
    p.updated_at         = datetime()
RETURN p.user_id AS user_id
"""

GET_PERSON = """
MATCH (p:Person {user_id: $user_id})
RETURN p
"""

GET_PERSON_PATTERNS = """
MATCH (p:Person {user_id: $user_id})-[:EXHIBITS]->(rp:RelationalPattern)
RETURN rp
ORDER BY rp.last_observed_at DESC
LIMIT $limit
"""

# ─────────────────────────────────────────────────────────────────────────────
# Couple queries
# ─────────────────────────────────────────────────────────────────────────────

UPSERT_COUPLE = """
MERGE (c:Couple {couple_id: $couple_id})
SET c.primary_cycle = $primary_cycle,
    c.eft_stage     = $eft_stage,
    c.updated_at    = datetime()
WITH c
MATCH (pa:Person {user_id: $partner_a_id})
MATCH (pb:Person {user_id: $partner_b_id})
MERGE (pa)-[:PARTNER_IN]->(c)
MERGE (pb)-[:PARTNER_IN]->(c)
RETURN c.couple_id AS couple_id
"""

GET_COUPLE_PATTERNS = """
MATCH (c:Couple {couple_id: $couple_id})-[:HAS_PATTERN]->(rp:RelationalPattern)
RETURN rp
ORDER BY rp.last_observed_at DESC
LIMIT $limit
"""

GET_COUPLE_CONTEXT = """
MATCH (c:Couple {couple_id: $couple_id})
OPTIONAL MATCH (c)-[:HAS_PATTERN]->(rp:RelationalPattern)
OPTIONAL MATCH (c)-[:EXPERIENCED]->(e:Event)
RETURN c, collect(DISTINCT rp) AS patterns, collect(DISTINCT e) AS events
"""

# ─────────────────────────────────────────────────────────────────────────────
# RelationalPattern queries
# ─────────────────────────────────────────────────────────────────────────────

UPSERT_RELATIONAL_PATTERN = """
MERGE (rp:RelationalPattern {pattern_id: $pattern_id})
SET rp.pattern_type      = $pattern_type,
    rp.description       = $description,
    rp.framework_tag     = $framework_tag,
    rp.confidence        = $confidence,
    rp.last_observed_at  = datetime()
ON CREATE SET rp.first_observed_at = datetime()
WITH rp
MATCH (p:Person {user_id: $user_id})
MERGE (p)-[:EXHIBITS]->(rp)
RETURN rp.pattern_id AS pattern_id
"""

LINK_PATTERN_TO_COUPLE = """
MATCH (rp:RelationalPattern {pattern_id: $pattern_id})
MATCH (c:Couple {couple_id: $couple_id})
MERGE (c)-[:HAS_PATTERN]->(rp)
"""

# ─────────────────────────────────────────────────────────────────────────────
# NeedCluster queries
# ─────────────────────────────────────────────────────────────────────────────

UPSERT_NEED_CLUSTER = """
MERGE (n:NeedCluster {need_id: $need_id})
SET n.needs              = $needs,
    n.intensity_signal   = $intensity_signal,
    n.expressed_directly = $expressed_directly,
    n.updated_at         = datetime()
WITH n
MATCH (p:Person {user_id: $user_id})
MERGE (p)-[:HAS_NEED]->(n)
RETURN n.need_id AS need_id
"""

# ─────────────────────────────────────────────────────────────────────────────
# Event queries
# ─────────────────────────────────────────────────────────────────────────────

CREATE_EVENT = """
CREATE (e:Event {
  event_id:         $event_id,
  event_type:       $event_type,
  theme:            $theme,
  resolution_signal: $resolution_signal,
  occurred_at:      datetime()
})
WITH e
MATCH (c:Couple {couple_id: $couple_id})
MERGE (c)-[:EXPERIENCED]->(e)
RETURN e.event_id AS event_id
"""

# ─────────────────────────────────────────────────────────────────────────────
# Agent R context query — read-only, aggregates relational intelligence
# ─────────────────────────────────────────────────────────────────────────────

GET_RELATIONSHIP_SUMMARY = """
MATCH (c:Couple {couple_id: $couple_id})
OPTIONAL MATCH (c)-[:HAS_PATTERN]->(rp:RelationalPattern)
OPTIONAL MATCH (c)-[:EXPERIENCED]->(e:Event)
OPTIONAL MATCH (pa:Person)-[:PARTNER_IN]->(c)
OPTIONAL MATCH (pa)-[:HAS_NEED]->(n:NeedCluster)
RETURN
  c.primary_cycle   AS primary_cycle,
  c.eft_stage       AS eft_stage,
  collect(DISTINCT {
    type: rp.pattern_type,
    description: rp.description,
    framework: rp.framework_tag,
    confidence: rp.confidence,
    last_seen: rp.last_observed_at
  }) AS patterns,
  collect(DISTINCT {
    type: e.event_type,
    theme: e.theme,
    resolution: e.resolution_signal
  }) AS events,
  collect(DISTINCT {
    user_id: pa.user_id,
    attachment: pa.attachment_style,
    regulation: pa.regulation_style,
    needs: n.needs
  }) AS partners
"""
