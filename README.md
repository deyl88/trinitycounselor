# Trinity Counselor

> *The relationship is the client.*

Trinity is a multi-agent AI relationship counseling system built on a **Trinity Architecture**: three AI agents that function as a unified relational intelligence, with ironclad privacy boundaries between each partner's private context.

This is not a chatbot. It is a new category of product — **AI-supported relational systems** — beginning with marriages and designed to extend to families, co-founders, leadership teams, and communities.

---

## The Core Insight

In relationships, there are three entities:
- **Person A**
- **Person B**
- **The relationship itself**

Traditional couples therapy sees each person through the others' eyes. Trinity gives each person their own private space — and holds the relationship as a living system, separate from either individual.

---

## Architecture

### The Three Agents

```
┌──────────────────────┐    ┌──────────────────────┐
│     Agent A          │    │     Agent B          │
│  Private Counselor   │    │  Private Counselor   │
│  for Partner A       │    │  for Partner B       │
│                      │    │                      │
│  • Full privacy      │    │  • Full privacy      │
│  • EFT-informed      │    │  • EFT-informed      │
│  • pgvector memory   │    │  • pgvector memory   │
│  • LangGraph state   │    │  • LangGraph state   │
└──────────┬───────────┘    └──────────┬───────────┘
           │  abstracted patterns only  │
           ▼                           ▼
    ┌──────────────────────────────────────────┐
    │         Privacy Mediator                 │
    │  (pattern synthesis — no raw content)    │
    └─────────────────────┬────────────────────┘
                          │
                          ▼
    ┌──────────────────────────────────────────┐
    │   Relational Knowledge Graph (RKG)       │
    │   Neo4j — abstracted patterns only       │
    │                                          │
    │  Person → RelationalPattern              │
    │  Couple → NeedCluster                    │
    │  Event  → TherapyFrameInsight            │
    └─────────────────────┬────────────────────┘
                          │
                          ▼
           ┌──────────────────────────┐
           │       Agent R            │
           │  Relationship Agent      │
           │  "The Third Presence"    │
           │                          │
           │  • No access to A or B   │
           │  • Reads only from RKG   │
           │  • Mediates joint sess.  │
           └──────────────────────────┘
```

### Agent R: The Third Presence

Agent R holds the relationship as its client — not either individual. It knows the shape of what is happening between partners (patterns, cycles, attachment signals) without knowing the private words either partner has used. It is the presence that holds both people, sees the whole, and cares for what is between them.

---

## Privacy Model (3 Layers)

```
Layer 1: Raw Private Store
  ├── Per-partner, per-session
  ├── Encrypted with AES-256-GCM using user-specific key
  ├── Never leaves the user's namespace
  └── Never accessible to Agent R or the other partner

Layer 2: Pattern Synthesis (Privacy Mediator)
  ├── Triggered when a solo session closes
  ├── Claude reads raw content (ephemerally, in-process only)
  ├── Extracts abstract patterns — no quotes, no identifiers
  └── Raw content discarded after synthesis

Layer 3: Relational Knowledge Graph (RKG)
  ├── Neo4j — relational-level insights only
  ├── "withdraw-pursue pattern active" — not "she said she hates me"
  ├── Read by Agent R to build its relational context
  └── Safe to share across the privacy boundary
```

---

## Therapeutic Framework

Trinity integrates insights from multiple evidence-based approaches:

| Framework | Application |
|-----------|-------------|
| **EFT** (Emotionally Focused Therapy) | Primary lens. Access primary emotions beneath reactive behaviors. Map attachment cycles. |
| **Attachment Theory** | Understand anxious, avoidant, disorganised patterns. Recognize attachment needs driving behavior. |
| **IFS** (Internal Family Systems) | Parts work. Meet the critic, the withdrawer, the exile. Curiosity over judgment. |
| **Gottman Method** | Four Horsemen detection. Repair attempts. Sound Relationship House. |
| **Esther Perel** | Desire, intimacy, aliveness in committed love. The long arc of sustained partnership. |
| **Family Systems Theory** | The couple as a living system. Symptoms as system signals. Cycles over individuals. |

---

## Session Types

| Type | Participants | Agent | Privacy |
|------|-------------|-------|---------|
| `solo_a` | Partner A | Agent A | Fully private to A |
| `solo_b` | Partner B | Agent B | Fully private to B |
| `joint` | A + B | Agent R | Both present; no private content |

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | Python 3.11 + FastAPI |
| Agent Framework | LangGraph (StateGraph + PostgresSaver) |
| LLM | Anthropic Claude (`claude-sonnet-4-6`) |
| Embeddings | OpenAI `text-embedding-3-small` |
| Vector / Long-term Memory | pgvector (per-user namespaced) |
| Relational Knowledge Graph | Neo4j 5.x |
| Auth | JWT (python-jose) + per-user AES-256-GCM |
| Frontend | React Native (Expo) |

---

## Project Structure

```
trinitycounselor/
├── backend/
│   ├── main.py                    # FastAPI app + lifespan
│   ├── config.py                  # Pydantic Settings
│   ├── agents/
│   │   ├── base_agent.py          # Shared LangGraph scaffolding
│   │   ├── agent_a.py             # Agent A — full LangGraph implementation
│   │   ├── agent_b.py             # Agent B
│   │   ├── agent_r.py             # Agent R (Relationship Agent)
│   │   └── prompts/               # EFT-informed system prompts
│   ├── api/
│   │   ├── middleware/auth.py     # JWT validation dependency
│   │   └── routes/                # agent_a, agent_b, agent_r, sessions
│   ├── privacy/
│   │   ├── encryption.py          # AES-256-GCM per-user encryption
│   │   ├── synthesizer.py         # Pattern synthesis (no raw content out)
│   │   └── mediator.py            # Insight Sync orchestrator
│   ├── memory/
│   │   ├── pgvector_store.py      # Long-term semantic memory (per-user)
│   │   └── conversation_store.py  # Encrypted message persistence
│   ├── graph/
│   │   ├── rkg_client.py          # Neo4j RKG interface
│   │   ├── schema.cypher          # Node/relationship definitions
│   │   └── queries.py             # Typed Cypher query library
│   ├── models/                    # SQLAlchemy ORM (User, Couple, Session, Message, Pattern)
│   ├── auth/                      # JWT issuance + per-user key management
│   └── db/                        # Postgres + Neo4j driver init
├── frontend/                      # React Native (Expo) skeleton
├── scripts/
│   ├── init_db.py                 # Bootstrap postgres + pgvector + checkpointer tables
│   └── seed_neo4j.py              # Bootstrap RKG constraints + indexes
├── tests/
├── docker-compose.yml             # postgres+pgvector, neo4j
└── pyproject.toml
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- Docker + Docker Compose
- Anthropic API key
- OpenAI API key (embeddings only)

### 1. Start infrastructure

```bash
docker compose up -d
```

This starts:
- PostgreSQL 16 with pgvector (`localhost:5432`)
- Neo4j 5.20 Community (`localhost:7474` browser, `localhost:7687` bolt)

### 2. Install Python dependencies

```bash
pip install -e ".[dev]"
```

### 3. Configure environment

```bash
cp .env.example .env
# Edit .env — fill in API keys and generate a MASTER_KEY
python -c "import secrets,base64; print(base64.urlsafe_b64encode(secrets.token_bytes(32)).decode())"
```

### 4. Initialise the database

```bash
python scripts/init_db.py
python scripts/seed_neo4j.py
```

### 5. Run the API

```bash
uvicorn backend.main:app --reload
```

API docs: http://localhost:8000/docs (only visible when `DEBUG=true`)

### 6. Run tests

```bash
pytest tests/ -v
```

---

## API Overview

### Auth
```
POST /sessions/auth/register   — register a user
POST /sessions/auth/login      — get JWT token
```

### Couple Management
```
POST /sessions/invite          — create invite code (Partner A)
POST /sessions/invite/accept   — accept invite (Partner B) → creates Couple
```

### Sessions
```
POST /sessions/                — create a new session (solo_a | solo_b | joint)
POST /sessions/{id}/close      — close session + trigger Insight Sync
GET  /sessions/{id}            — get session metadata
```

### Agent Chat
```
POST /agent-a/chat             — Partner A ↔ Agent A (private)
POST /agent-b/chat             — Partner B ↔ Agent B (private)
POST /agent-r/chat             — Either partner ↔ Agent R (relational overview)
POST /agent-r/joint            — Joint session message (both partners + Agent R)
```

---

## Memory Architecture

```
Within a session (short-term):
  LangGraph PostgresSaver checkpointer
  → keyed by thread_id = "{user_id}:{session_id}"
  → stores full message history + graph state
  → automatic multi-turn continuity

Across sessions (long-term):
  pgvector store (per-user namespace)
  → stores abstracted session summaries
  → retrieved by semantic similarity on each new message
  → injected into system prompt as "context from past sessions"

Relational intelligence (cross-boundary):
  Neo4j RKG
  → abstracted patterns only
  → queried by Agent R at the start of every invocation
  → never contains raw content
```

---

## Future Expansion

Trinity's architecture is designed to extend beyond couples:

- **Families** — a family system with individual agents per member + family mediator
- **Co-founders** — professional relationships with different therapeutic framing
- **Leadership teams** — group dynamics, power, trust, psychological safety
- **Friend groups** — peer relationships, conflict repair
- **Communities** — scaled relational intelligence for larger systems

The pattern: *N individual private agents + 1 system-level mediator agent + 1 shared RKG*.

---

## Ethical Considerations

- **Not a replacement for therapy.** Trinity is a between-session support tool. It should recommend professional human therapists for crisis situations.
- **Privacy by design.** The system is architected so that raw content cannot cross the privacy boundary — this is enforced at the code level, not just policy level.
- **Consent.** Both partners must actively opt in. Couple linking requires explicit invite + accept.
- **Data sovereignty.** Per-user encryption keys mean data is meaningless without the user's credential chain.
- **No permanence of pain.** The system should never store crisis disclosures in a way that creates legal liability. (Future: crisis detection + referral pipeline.)
- **Transparency.** Users should understand what the system knows and can request deletion.

---

## License

Private / proprietary — all rights reserved.
