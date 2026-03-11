// ═══════════════════════════════════════════════════════════════════════════
// Trinity Counselor — Relational Knowledge Graph (RKG) Schema
// Neo4j 5.x Cypher
//
// Run via: scripts/seed_neo4j.py (applies constraints + indexes)
//
// Privacy note: This graph holds ONLY abstracted relational intelligence.
// No raw conversation content, no direct quotes, no identifiable statements.
// ═══════════════════════════════════════════════════════════════════════════

// ── Constraints (uniqueness + existence) ────────────────────────────────────

CREATE CONSTRAINT person_id_unique IF NOT EXISTS
  FOR (p:Person) REQUIRE p.user_id IS UNIQUE;

CREATE CONSTRAINT couple_id_unique IF NOT EXISTS
  FOR (c:Couple) REQUIRE c.couple_id IS UNIQUE;

CREATE CONSTRAINT pattern_id_unique IF NOT EXISTS
  FOR (rp:RelationalPattern) REQUIRE rp.pattern_id IS UNIQUE;

CREATE CONSTRAINT need_id_unique IF NOT EXISTS
  FOR (n:NeedCluster) REQUIRE n.need_id IS UNIQUE;

CREATE CONSTRAINT event_id_unique IF NOT EXISTS
  FOR (e:Event) REQUIRE e.event_id IS UNIQUE;

CREATE CONSTRAINT insight_id_unique IF NOT EXISTS
  FOR (i:TherapyFrameInsight) REQUIRE i.insight_id IS UNIQUE;

// ── Indexes ──────────────────────────────────────────────────────────────────

CREATE INDEX person_couple_idx IF NOT EXISTS FOR (p:Person) ON (p.couple_id);
CREATE INDEX pattern_type_idx IF NOT EXISTS FOR (rp:RelationalPattern) ON (rp.pattern_type);
CREATE INDEX event_type_idx IF NOT EXISTS FOR (e:Event) ON (e.event_type);
CREATE INDEX insight_framework_idx IF NOT EXISTS FOR (i:TherapyFrameInsight) ON (i.framework);

// ═══════════════════════════════════════════════════════════════════════════
// NODE DEFINITIONS (with example MERGE patterns)
// ═══════════════════════════════════════════════════════════════════════════

// ── Person ───────────────────────────────────────────────────────────────────
// Represents one partner in the system.
// Properties describe their relational profile — abstracted, never raw content.
//
// MERGE (p:Person {user_id: $user_id})
// SET p += {
//   display_name_hash: $display_name_hash,   // SHA-256 of display name — never plaintext
//   attachment_style: $attachment_style,      // anxious | avoidant | secure | disorganised
//   emotional_vocabulary_level: $level,       // low | medium | high
//   primary_love_language: $language,         // words | acts | gifts | time | touch
//   regulation_style: $style,                 // dysregulates | co-regulates | self-regulates
//   updated_at: datetime()
// }

// ── Couple ───────────────────────────────────────────────────────────────────
// The relationship entity — the primary "client" of the system.
//
// MERGE (c:Couple {couple_id: $couple_id})
// SET c += {
//   relationship_stage: $stage,              // forming | storming | norming | performing
//   primary_cycle: $cycle,                   // pursue-withdraw | attack-attack | freeze-freeze
//   gottman_horsemen_active: $horsemen,      // [criticism, contempt, defensiveness, stonewalling]
//   eft_stage: $eft_stage,                   // de-escalation | restructuring | consolidation
//   updated_at: datetime()
// }

// ── RelationalPattern ─────────────────────────────────────────────────────────
// A recurring dynamic between the couple OR within one partner.
//
// MERGE (rp:RelationalPattern {pattern_id: $pattern_id})
// SET rp += {
//   pattern_type: $type,                     // conflict | communication | attachment | etc.
//   description: $description,               // abstract description — no raw content
//   frequency_signal: $freq,                 // rare | occasional | frequent | chronic
//   framework_tag: $tag,                     // EFT | Gottman | IFS | Attachment | etc.
//   confidence: $confidence,
//   first_observed_at: datetime(),
//   last_observed_at: datetime()
// }

// ── NeedCluster ──────────────────────────────────────────────────────────────
// A cluster of unmet relational needs for a person.
//
// MERGE (n:NeedCluster {need_id: $need_id})
// SET n += {
//   needs: $needs,                           // [safety, connection, autonomy, recognition, etc.]
//   intensity_signal: $intensity,            // mild | moderate | acute
//   expressed_directly: $direct,             // true | false
//   updated_at: datetime()
// }

// ── Event ────────────────────────────────────────────────────────────────────
// A significant relational event (conflict, repair, breakthrough).
//
// MERGE (e:Event {event_id: $event_id})
// SET e += {
//   event_type: $type,                       // conflict | repair | breakthrough | rupture
//   theme: $theme,                           // abstract theme — no specifics
//   resolution_signal: $resolution,          // unresolved | partial | resolved
//   occurred_at: datetime()
// }

// ── TherapyFrameInsight ───────────────────────────────────────────────────────
// A tagged insight from a specific therapy framework.
//
// MERGE (i:TherapyFrameInsight {insight_id: $insight_id})
// SET i += {
//   framework: $framework,                   // EFT | Gottman | IFS | Attachment | Esther_Perel | FamilySystems
//   insight_text: $text,                     // clinically abstracted observation
//   confidence: $confidence,
//   created_at: datetime()
// }

// ═══════════════════════════════════════════════════════════════════════════
// RELATIONSHIP DEFINITIONS
// ═══════════════════════════════════════════════════════════════════════════

// (Person)-[:PARTNER_IN]->(Couple)
// (Person)-[:EXHIBITS]->(RelationalPattern)
// (Couple)-[:HAS_PATTERN]->(RelationalPattern)
// (Person)-[:HAS_NEED]->(NeedCluster)
// (Couple)-[:EXPERIENCED]->(Event)
// (Person)-[:PARTICIPATED_IN]->(Event)
// (RelationalPattern)-[:TAGGED_WITH]->(TherapyFrameInsight)
// (Event)-[:ILLUMINATED]->(RelationalPattern)
// (NeedCluster)-[:TRIGGERS]->(RelationalPattern)
