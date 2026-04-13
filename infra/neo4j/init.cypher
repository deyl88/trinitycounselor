// Trinity RKG — Initial Neo4j Schema
// ─────────────────────────────────────────────────────────────────────────────
// This file is mounted into the Neo4j container and run on first start.
// It is idempotent — IF NOT EXISTS guards prevent duplicate errors.
//
// The full schema initialization (including seed data) is also handled by
// app/rkg/schema.py which runs on every backend startup.
// This file serves as the authoritative DDL reference and a fallback init
// path for environments where the backend isn't running during DB setup.
// ─────────────────────────────────────────────────────────────────────────────

// ── Constraints (implicit indexes on id fields) ───────────────────────────────

CREATE CONSTRAINT person_id IF NOT EXISTS
  FOR (p:Person) REQUIRE p.id IS UNIQUE;

CREATE CONSTRAINT relationship_id IF NOT EXISTS
  FOR (r:Relationship) REQUIRE r.id IS UNIQUE;

CREATE CONSTRAINT pattern_id IF NOT EXISTS
  FOR (rp:RelationalPattern) REQUIRE rp.id IS UNIQUE;

CREATE CONSTRAINT need_id IF NOT EXISTS
  FOR (n:NeedCluster) REQUIRE n.id IS UNIQUE;

CREATE CONSTRAINT event_id IF NOT EXISTS
  FOR (e:Event) REQUIRE e.id IS UNIQUE;

CREATE CONSTRAINT insight_id IF NOT EXISTS
  FOR (t:TherapyFrameInsight) REQUIRE t.id IS UNIQUE;


// ── Lookup indexes ────────────────────────────────────────────────────────────

CREATE INDEX person_attachment IF NOT EXISTS
  FOR (p:Person) ON (p.attachment_style);

CREATE INDEX pattern_category IF NOT EXISTS
  FOR (rp:RelationalPattern) ON (rp.category);

CREATE INDEX pattern_intensity IF NOT EXISTS
  FOR (rp:RelationalPattern) ON (rp.intensity);

CREATE INDEX event_type IF NOT EXISTS
  FOR (e:Event) ON (e.type);

CREATE INDEX event_timestamp IF NOT EXISTS
  FOR (e:Event) ON (e.timestamp);

CREATE INDEX insight_framework IF NOT EXISTS
  FOR (t:TherapyFrameInsight) ON (t.framework);

CREATE INDEX relationship_status IF NOT EXISTS
  FOR (r:Relationship) ON (r.status);


// ── Seed: TherapyFrameInsight canonical nodes ─────────────────────────────────
// These are reused across all relationships via TAGGED_WITH edges.
// Created once, never deleted.

// EFT
MERGE (t:TherapyFrameInsight {id: 'eft:attachment_injury'})
  ON CREATE SET t.framework = 'EFT', t.tag = 'attachment_injury',
    t.description = 'A key moment where one partner felt abandoned or betrayed.';

MERGE (t:TherapyFrameInsight {id: 'eft:pursue_withdraw'})
  ON CREATE SET t.framework = 'EFT', t.tag = 'pursue_withdraw',
    t.description = 'Classic EFT dance: one partner pursues, the other withdraws.';

MERGE (t:TherapyFrameInsight {id: 'eft:emotional_accessibility'})
  ON CREATE SET t.framework = 'EFT', t.tag = 'emotional_accessibility',
    t.description = 'Ability to be emotionally present and reachable for a partner.';

MERGE (t:TherapyFrameInsight {id: 'eft:emotional_responsiveness'})
  ON CREATE SET t.framework = 'EFT', t.tag = 'emotional_responsiveness',
    t.description = 'Attunement and response to a partner''s emotional cues.';

// Gottman
MERGE (t:TherapyFrameInsight {id: 'gottman:criticism'})
  ON CREATE SET t.framework = 'Gottman', t.tag = 'criticism',
    t.description = 'Attacking the partner''s character rather than specific behavior.';

MERGE (t:TherapyFrameInsight {id: 'gottman:contempt'})
  ON CREATE SET t.framework = 'Gottman', t.tag = 'contempt',
    t.description = 'Eye-rolling, sarcasm, mockery — the strongest predictor of divorce.';

MERGE (t:TherapyFrameInsight {id: 'gottman:defensiveness'})
  ON CREATE SET t.framework = 'Gottman', t.tag = 'defensiveness',
    t.description = 'Counter-attack or innocent victim stance to deflect criticism.';

MERGE (t:TherapyFrameInsight {id: 'gottman:stonewalling'})
  ON CREATE SET t.framework = 'Gottman', t.tag = 'stonewalling',
    t.description = 'Emotional shutdown and withdrawal from interaction.';

MERGE (t:TherapyFrameInsight {id: 'gottman:repair_attempt'})
  ON CREATE SET t.framework = 'Gottman', t.tag = 'repair_attempt',
    t.description = 'Any action attempting to de-escalate negativity during conflict.';

MERGE (t:TherapyFrameInsight {id: 'gottman:love_map'})
  ON CREATE SET t.framework = 'Gottman', t.tag = 'love_map',
    t.description = 'Knowledge of partner''s inner world, needs, and dreams.';

// IFS
MERGE (t:TherapyFrameInsight {id: 'ifs:protector_activated'})
  ON CREATE SET t.framework = 'IFS', t.tag = 'protector_activated',
    t.description = 'A protective inner part taking over to prevent vulnerability.';

MERGE (t:TherapyFrameInsight {id: 'ifs:exile_triggered'})
  ON CREATE SET t.framework = 'IFS', t.tag = 'exile_triggered',
    t.description = 'Wounded exile part activated, driving intense emotional reaction.';

MERGE (t:TherapyFrameInsight {id: 'ifs:self_led'})
  ON CREATE SET t.framework = 'IFS', t.tag = 'self_led',
    t.description = 'Partner responding from Self — calm, curious, compassionate.';

// Attachment
MERGE (t:TherapyFrameInsight {id: 'attachment:anxious'})
  ON CREATE SET t.framework = 'Attachment', t.tag = 'anxious_style',
    t.description = 'Anxious attachment: hyperactivation of the attachment system.';

MERGE (t:TherapyFrameInsight {id: 'attachment:avoidant'})
  ON CREATE SET t.framework = 'Attachment', t.tag = 'avoidant_style',
    t.description = 'Avoidant attachment: deactivation of the attachment system.';

MERGE (t:TherapyFrameInsight {id: 'attachment:secure'})
  ON CREATE SET t.framework = 'Attachment', t.tag = 'secure_base',
    t.description = 'Moment of secure functioning — felt safety with the partner.';

MERGE (t:TherapyFrameInsight {id: 'attachment:disorganized'})
  ON CREATE SET t.framework = 'Attachment', t.tag = 'disorganized_style',
    t.description = 'Disorganized attachment: fear of the attachment figure.';
