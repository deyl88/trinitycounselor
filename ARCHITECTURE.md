# Trinity Counselor — System Architecture

**Version:** 0.1
**Classification:** Product Architecture + Technical Design

---

## Executive Summary

Trinity Counselor is a multi-agent AI system that treats the *relationship* as the primary client. It deploys three coordinated AI agents — one for each partner and one for the relationship itself — that share abstracted relational insight while preserving strict psychological safety boundaries. The result is continuous, context-aware couples support that no human therapist can provide at scale.

---

## 1. High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         TRINITY SYSTEM                              │
│                                                                     │
│  ┌─────────────────┐    ┌──────────────────┐    ┌───────────────┐  │
│  │  Partner A      │    │  RELATIONSHIP    │    │  Partner B    │  │
│  │  Counselor      │◄──►│  INTELLIGENCE   │◄──►│  Counselor    │  │
│  │  (Agent A)      │    │  LAYER (RIL)    │    │  (Agent B)    │  │
│  └────────┬────────┘    └────────┬─────────┘    └───────┬───────┘  │
│           │                      │                       │          │
│     [Private]              [Shared Layer]          [Private]        │
│     Context A              Pattern Store           Context B        │
│                                  │                                  │
│                    ┌─────────────┴──────────────┐                  │
│                    │  Relational Context Engine  │                  │
│                    │  (RCE)                      │                  │
│                    └─────────────────────────────┘                  │
└─────────────────────────────────────────────────────────────────────┘
         │                        │                        │
    Partner A UI            Joint Session UI          Partner B UI
```

### Core Layers

| Layer | Role |
|-------|------|
| **Agent A / Agent B** | Private counselors. Full access to their partner's private context. Zero access to the other's private context. |
| **Relationship Intelligence Layer (RIL)** | Receives abstracted signals from both agents. Maintains the relational model. Powers the Relationship Counselor. |
| **Relational Context Engine (RCE)** | Long-term memory, pattern detection, dynamics modeling, therapy framework application. |
| **Privacy Firewall** | Enforces unidirectional abstraction. Raw private content never flows outward. |

---

## 2. Multi-Agent Interaction Model

### Agent Roles and Boundaries

```
Agent A (Private)                       Agent B (Private)
├── Reads: Partner A's full history     ├── Reads: Partner B's full history
├── Writes: Partner A's private store   ├── Writes: Partner B's private store
├── Emits: Abstracted signals → RIL     ├── Emits: Abstracted signals → RIL
└── Cannot: Access Partner B's data     └── Cannot: Access Partner A's data

Relationship Counselor (Shared)
├── Reads: RIL pattern store (abstracted)
├── Reads: Joint session history
├── Writes: Relationship model updates
├── Interacts: With A alone, B alone, or both together
└── Cannot: Access either partner's private raw data
```

### Agent Communication Protocol

Agents communicate **only through the RIL**, never directly peer-to-peer. Communication uses a **Signal Abstraction Protocol (SAP)**:

```
Raw private statement (Agent A context):
  "I feel like my partner never listens to me and I'm exhausted."

SAP extraction (emitted to RIL):
  {
    "signal_type": "emotional_state",
    "themes": ["feeling_unheard", "emotional_exhaustion"],
    "intensity": 0.82,
    "category": "connection_deficit",
    "source": "partner_a",  // only source tag, no content
    "timestamp": "2024-03-01T14:23:00Z"
  }
```

The RIL aggregates signals over time into a **relational dynamic model** — no raw content ever leaves the private context.

### Session Modes

| Mode | Participants | Agent Used | Privacy Level |
|------|-------------|------------|---------------|
| **Solo A** | Partner A only | Agent A | Fully private |
| **Solo B** | Partner B only | Agent B | Fully private |
| **Guided A** | Partner A + Relationship view | Rel. Counselor | Abstracted |
| **Guided B** | Partner B + Relationship view | Rel. Counselor | Abstracted |
| **Joint Session** | Both partners | Rel. Counselor (mediator) | Shared/negotiated |
| **Check-in** | Either partner | Agent A or B | Private |

---

## 3. Privacy-Preserving Information Sharing

### The Privacy Firewall

This is the most critical architectural component. It ensures that the system can accumulate relational wisdom without exposing private disclosures.

```
┌─────────────────── PRIVACY FIREWALL ───────────────────────┐
│                                                             │
│  PRIVATE ZONE                    │  SHARED ZONE            │
│  ─────────────                   │  ───────────            │
│  • Raw messages                  │  • Theme vectors         │
│  • Journal entries               │  • Pattern scores        │
│  • Emotional disclosures         │  • Dynamic models        │
│  • Partner-specific history      │  • Aggregated signals    │
│                                  │  • Joint session logs    │
│         ─────────────────────────►                          │
│              One-way only.                                  │
│              Via SAP extraction.                            │
│              No reconstruction possible.                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Signal Abstraction Protocol (SAP) — Detailed

The SAP processes private content through three transformations:

**Step 1 — Theme Extraction**
Using an LLM in a sandboxed context, extract themes from private content. The extractor has no system prompt access to cross-partner data.

**Step 2 — Intensity + Category Scoring**
Score emotional intensity (0.0–1.0) and assign to categorical taxonomy (connection, respect, trust, safety, intimacy, communication, shared_purpose, resentment, grief, etc.)

**Step 3 — Temporal Aggregation**
Individual signals are aggregated into rolling windows (7-day, 30-day, 90-day). Individual signal access expires after aggregation. The raw signal becomes unreachable.

### Consent-Controlled Sharing

Partners can voluntarily **elevate** private insights to shared context:

```
Partner A can choose to share:
  [Private] "I've been feeling disconnected for months."
         ↓ (partner explicitly shares this)
  [Shared] "Partner A wants to share: feeling of disconnection over recent months."
```

This is the only path for raw content to cross the firewall, and it requires explicit affirmative action.

---

## 4. Data Model for Relational Dynamics

### Core Schemas

```typescript
// ── Partner Profile ──────────────────────────────────────────────
interface PartnerProfile {
  id: string;
  relationship_id: string;

  // Attachment & style
  attachment_style: "secure" | "anxious" | "avoidant" | "disorganized" | null;
  communication_style: string[];
  love_languages: string[];

  // Pattern tracking
  emotional_patterns: EmotionalPattern[];
  recurring_themes: ThemeRecord[];
  triggers: TriggerRecord[];
  unmet_needs: NeedRecord[];

  // Progress
  growth_edges: string[];
  strengths: string[];

  // Private store reference (encrypted, isolated)
  private_context_id: string;
}

// ── Relational Dynamic Model ─────────────────────────────────────
interface RelationshipModel {
  id: string;
  partner_a_id: string;
  partner_b_id: string;
  created_at: Date;

  // Current state
  health_dimensions: {
    connection: DimensionScore;
    trust: DimensionScore;
    communication: DimensionScore;
    intimacy: DimensionScore;
    shared_purpose: DimensionScore;
    safety: DimensionScore;
  };

  // Pattern library
  conflict_patterns: ConflictPattern[];
  repair_history: RepairEvent[];
  breakthrough_moments: BreakthroughRecord[];

  // Trajectory
  trend_7d: TrendVector;
  trend_30d: TrendVector;
  trend_90d: TrendVector;

  // Active themes surfaced by RIL
  active_themes: ActiveTheme[];
  recommended_focus: string[];
}

// ── RIL Signal ───────────────────────────────────────────────────
interface RILSignal {
  id: string;
  relationship_id: string;
  source: "partner_a" | "partner_b";
  signal_type: "emotional_state" | "need" | "conflict" | "repair" | "growth";
  themes: string[];
  intensity: number; // 0.0 - 1.0
  category: ThemeCategory;
  framework_tags: TherapyFramework[];
  timestamp: Date;
  aggregated: boolean; // true = raw signal no longer accessible
}

// ── Joint Session ────────────────────────────────────────────────
interface JointSession {
  id: string;
  relationship_id: string;
  started_at: Date;
  session_type: "check_in" | "conflict_repair" | "deepening" | "planning";
  exchanges: SessionExchange[];
  counselor_observations: string[];
  outcomes: SessionOutcome[];
  follow_up_tasks: FollowUpTask[];
}

// ── Dimension Score ──────────────────────────────────────────────
interface DimensionScore {
  current: number;       // 0.0 - 1.0
  trend: "improving" | "stable" | "declining";
  last_updated: Date;
  confidence: number;    // based on signal volume
  signals_30d: number;
}
```

### Therapy Framework Taxonomy

The system tags signals and observations with therapy framework labels to inform counselor responses:

```typescript
type TherapyFramework =
  | "gottman_four_horsemen"    // Criticism, contempt, defensiveness, stonewalling
  | "gottman_repair"           // Repair attempt detection
  | "eft_cycle"                // Emotionally Focused Therapy attachment cycle
  | "eft_emotion_sphere"       // Primary vs secondary emotions
  | "ifs_part"                 // Internal Family Systems — parts language
  | "attachment_activated"     // Attachment system triggered
  | "systems_feedback_loop"    // Family Systems circular patterns
  | "perel_desire_distance"    // Desire, distance, aliveness themes
  | "grief_loss"               // Grief within relationship context
  | "shame_spiral"             // Shame-based withdrawal patterns
```

---

## 5. Product Experience Flow

### Onboarding Flow

```
1. Relationship Registration
   └── Both partners invited (one starts, one joins via link)

2. Individual Intake (private, each partner separately)
   ├── Background + relationship history
   ├── Attachment style assessment (brief questionnaire)
   ├── Current pain points and hopes
   └── Communication preferences

3. Relationship Calibration
   ├── Brief joint introduction session
   ├── Both partners share what they hope to gain
   └── Relationship Counselor introduces itself

4. First Solo Sessions
   ├── Agent A meets Partner A privately
   ├── Agent B meets Partner B privately
   └── Deep-dive emotional context building begins
```

### Daily Experience

```
Morning Check-in (Solo, ~3 min)
  └── "How are you feeling about your relationship today?"
      ├── Mood tracking → feeds RIL
      ├── Any overnight thoughts to process?
      └── One micro-reflection prompt

Triggered Support (Real-time, async)
  └── "Something just happened. I need to process this."
      ├── Free-form journaling to private counselor
      ├── Agent guides toward emotional clarity
      └── Conflict de-escalation prompts if needed

Weekly Relationship Session (Joint, 20-30 min)
  └── Relationship Counselor facilitates
      ├── Reviews themes from the week (abstracted)
      ├── Structured dialogue exercise
      ├── Repair conversation if needed
      └── Sets intentions for the coming week
```

### Conflict Mode

When either partner signals distress/conflict, the system enters **Conflict Mode**:

```
Partner A (in private): "We just had a big fight about money."
    ↓
Agent A: "I'm here. Let's process this. What happened from your perspective?"
    [Private emotional processing session]
    ↓
Agent A emits signal: {themes: ["financial_conflict", "feeling_unheard"], intensity: 0.78}
    ↓
RIL updates → Relationship Counselor notified
    ↓
When Partner B opens app:
Agent B (private): "I understand there may have been some tension. Do you want to talk?"
    ↓
Later — Relationship Counselor (joint):
"I've been sensing some financial stress in the relationship this week.
 Would this be a good time to work through it together?"
```

---

## 6. Technical Stack Options

### Option A — Pragmatic MVP Stack

Best for: **fastest path to working prototype**

```
Layer           Technology
──────────────────────────────────────────────────────
LLM Backend     Anthropic Claude API (claude-sonnet-4-6)
Orchestration   LangChain or LlamaIndex (agent coordination)
Backend API     FastAPI (Python) — REST + WebSocket
Database        PostgreSQL (structured data)
Vector Store    pgvector or Pinecone (embeddings/RAG)
Private Store   AES-256 encrypted Postgres partitions
Auth            Supabase Auth or Auth0
Frontend        Next.js + React
Mobile          React Native (later phase)
Hosting         Vercel (frontend) + Railway/Fly.io (backend)
Queue           Redis + Celery (async signal processing)
```

### Option B — Production-Grade Stack

Best for: **scalability + security at volume**

```
Layer           Technology
──────────────────────────────────────────────────────
LLM Backend     Anthropic Claude API + fine-tuned adapters
Orchestration   Custom agent framework (recommended over LangChain)
Backend         FastAPI (Python) microservices
                ├── Agent Service (A/B/Relationship)
                ├── RIL Service (signal processing)
                ├── Privacy Service (SAP execution)
                └── Session Service
Database        PostgreSQL (primary) + Redis (cache/queues)
Vector Store    Pinecone (managed) or Weaviate (self-hosted)
Private Store   Separate encrypted DB per relationship
                (cryptographic isolation, not just access control)
Auth            Auth0 with MFA required
Frontend        Next.js 14 (App Router)
Mobile          React Native + Expo
Infra           AWS (ECS Fargate + RDS + ElastiCache)
Observability   Datadog or OpenTelemetry
Compliance      SOC2 Type II path from day one
```

### Recommended for Prototype

Start with **Option A** but architect the privacy layer as if it's **Option B** from day one. The privacy model is the product's core differentiation — it must be correct before anything else.

---

## 7. Biggest Technical Challenges

### Challenge 1 — The Privacy Paradox

The system's value comes from shared relational intelligence. Its trust comes from true privacy. These are in direct tension.

The SAP must be:
- **Lossy enough** that no private content can be reconstructed from signals
- **Informative enough** that the relationship model is genuinely useful

This requires careful empirical tuning. Initial approach: use an LLM in zero-shot mode to extract only categorical themes, never paraphrase or quote. Subject the extraction to adversarial testing — can a reconstructor recover private content from the signals alone?

### Challenge 2 — Agent Identity and Consistency

Each agent must maintain a consistent therapeutic persona across sessions spanning months or years. With stateless LLM calls, this requires careful:
- Prompt engineering (persona, style, framework preferences)
- Context window management (what to include from history)
- Memory compression without losing therapeutic continuity

Approach: Maintain a **rolling therapeutic summary** — a living document per partner summarizing key insights, current themes, and therapeutic direction. Include this in every agent prompt.

### Challenge 3 — The Joint Session Coordination Problem

In joint sessions, the Relationship Counselor must:
- Reference patterns from both partners' histories
- Translate each partner's perspective for the other
- Do all this without revealing private content

This requires the Relationship Counselor to operate from a carefully constructed context window containing only:
- The relational model (abstracted)
- The joint session history
- Current active themes from RIL
- Negotiated/consented shared insights

No private context should ever enter this prompt.

### Challenge 4 — Crisis Detection and Escalation

The system will encounter genuine mental health crises:
- Domestic violence signals
- Suicidal ideation
- Severe depression or trauma

The system must:
- Detect these signals reliably (both explicit and implicit)
- Have a clear escalation path to human crisis resources
- Never attempt to handle acute crisis autonomously

This requires integration with crisis APIs (Crisis Text Line, etc.) and careful prompt-level safeguards.

### Challenge 5 — Measuring Relational Health

The DimensionScore model requires reliable signal-to-score mapping. What does a "connection" score of 0.65 actually mean? How is it computed?

Approach: Use a **Bayesian belief model** updated by incoming signals. Scores are probability distributions over health states, not point estimates. Weight signals by recency and intensity. Validate scoring against clinical instruments (e.g., ADOS-2 adapted for couples, Gottman's Relationship Checkup).

---

## 8. Risks and Ethical Considerations

### Critical Risks

| Risk | Description | Mitigation |
|------|-------------|------------|
| **Weaponization** | Partner A uses their counselor to build a manipulation strategy against Partner B | Agent prompts explicitly prohibit adversarial coaching; detect pattern of manipulation-seeking |
| **False Safety** | Users believe the system is a substitute for crisis intervention | Clear clinical boundaries stated in onboarding; mandatory escalation for crisis signals |
| **Privacy Breach** | Technical failure exposes private data across the firewall | Cryptographic isolation (not just access control); penetration testing; bug bounty program |
| **Bias** | System reinforces gendered or cultural relationship norms | Diverse training data; explicit neutrality in relationship counselor persona; cultural adaptation layer |
| **Dependency** | Partners become psychologically dependent on AI mediation | Build toward user autonomy; celebrate when users need the system less; not-engagement metrics |
| **Legal Liability** | Advice construed as clinical therapy | Clear product positioning as "reflective tool" not therapy; no diagnostic language; mandatory disclaimers |
| **Data Subpoena** | Private journal data subpoenaed in divorce proceedings | End-to-end encryption; zero-knowledge architecture option; legal policy for data requests |

### Ethical Principles

The system must be designed around these commitments:

1. **The relationship is the client, not either partner.** The system should not optimize for either partner's individual satisfaction at the expense of the other.

2. **Consent is continuous, not one-time.** Partners can withdraw from the system at any time. Their private data is deleted within 30 days.

3. **The system supports human agency, not replaces it.** AI insight should help partners think more clearly, not replace their thinking.

4. **Honesty over flattery.** The system should surface difficult truths, not just validate whatever partners present.

5. **No engagement optimization.** The product must not optimize for daily active users. It should optimize for relationship health outcomes. This is a fundamental product principle that conflicts with typical startup metrics.

---

## 9. Prototype Approach

### Phase 0 — Single-Partner Prototype (2 weeks)

Prove the core counseling loop before building multi-agent complexity.

```
Build:
  • One AI counselor agent (Claude API)
  • Persistent conversation with rolling therapeutic summary
  • Theme extraction from conversations
  • Basic web UI (Next.js)

Validate:
  • Does the counselor feel like a real counselor?
  • Does the therapeutic summary stay coherent over time?
  • Does theme extraction produce useful, non-identifying signals?
```

### Phase 1 — Trinity MVP (4–6 weeks)

```
Build:
  • Three-agent architecture (A, B, Relationship)
  • Privacy firewall + SAP
  • Basic relational model (3-5 dimensions)
  • Solo and joint session modes
  • Two-person onboarding flow

Validate:
  • Do couples feel the system understands their relationship?
  • Is privacy maintained perceptually and technically?
  • Does the joint session counselor feel neutral and insightful?
```

### Phase 2 — Relational Intelligence (8–12 weeks)

```
Build:
  • Full RCE with pattern detection
  • Trend analysis and health dimension scoring
  • Conflict Mode
  • Therapy framework tagging
  • Crisis detection and escalation

Validate:
  • Does pattern detection surface real insights?
  • Do couples report feeling understood over time?
  • Clinical review of crisis detection accuracy
```

### Prototype Stack (Phase 0–1)

```python
# Minimal viable agent implementation sketch

from anthropic import Anthropic

client = Anthropic()

PARTNER_A_SYSTEM = """
You are a private, compassionate counselor supporting Partner A.
You hold a safe, confidential space for them to process their relationship.
You listen deeply, ask clarifying questions, and reflect patterns back.
You are trained in EFT, Gottman Method, and Attachment Theory.
Nothing shared here will be shown to their partner.
You maintain a therapeutic summary of your ongoing work together.

Current therapeutic context:
{therapeutic_summary}
"""

RELATIONSHIP_SYSTEM = """
You are the Relationship Counselor — you hold the relationship itself as your client.
You see both partners with deep compassion and strict neutrality.
You help both partners feel understood and help them understand each other.
You never reveal private disclosures. You speak in themes and patterns.
You are trained in EFT, Gottman Method, Family Systems, and Esther Perel's work.

Current relational context:
{relational_model}

Active themes (abstracted from both partners):
{active_themes}
"""

class TrinityAgent:
    def __init__(self, role: str, system_template: str):
        self.role = role
        self.system_template = system_template
        self.conversation_history = []
        self.therapeutic_summary = ""

    def respond(self, user_message: str, context: dict) -> str:
        system = self.system_template.format(**context)
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=system,
            messages=self.conversation_history
        )
        assistant_message = response.content[0].text
        self.conversation_history.append({
            "role": "assistant",
            "content": assistant_message
        })
        return assistant_message

    def extract_themes(self, recent_messages: list[str]) -> list[dict]:
        """Extract abstracted relational signals from private conversation."""
        extraction_prompt = f"""
        Analyze these messages and extract relational themes.
        Return ONLY a JSON array of theme objects.
        Do NOT quote or paraphrase specific statements.

        Messages: {recent_messages}

        Format: [{{"theme": "string", "category": "string", "intensity": 0.0-1.0}}]
        """
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=512,
            system="You extract relational themes. You never quote source content.",
            messages=[{"role": "user", "content": extraction_prompt}]
        )
        return response.content[0].text  # parse JSON in production
```

---

## Appendix: Therapy Framework Reference

| Framework | Key Concepts | Application in Trinity |
|-----------|-------------|----------------------|
| **Gottman Method** | Four Horsemen, repair attempts, Love Maps, bids for connection | Detect communication patterns; coach repair attempts |
| **EFT (Sue Johnson)** | Attachment cycles, primary/secondary emotions, "are you there for me?" | Reframe conflicts as attachment needs; de-escalation |
| **Internal Family Systems** | Parts, exiles, protectors, the Self | Individual self-awareness work in private sessions |
| **Family Systems (Bowen)** | Differentiation, triangulation, emotional fusion | Identify enmeshment vs. disconnection patterns |
| **Attachment Theory** | Secure/anxious/avoidant/disorganized styles | Inform individual counselor approach to each partner |
| **Esther Perel** | Desire, aliveness, erotic intelligence, contrasting needs | Long-term relationship vitality; intimacy conversations |

---

*"In this system, the relationship is the client. The goal is to build an intelligence that can hold and care for that relationship over time."*
