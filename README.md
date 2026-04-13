# Trinity Counselor

A multi-agent AI relationship counseling system where **the relationship is the client**.

Trinity deploys three coordinated AI agents — one private counselor per partner plus one for the relationship itself — that share abstracted relational insight while preserving strict psychological safety boundaries.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                           TRINITY SYSTEM                            │
│                                                                     │
│  ┌──────────────────┐   ┌───────────────────┐   ┌───────────────┐  │
│  │  Agent A         │   │  Privacy Mediator  │   │  Agent B      │  │
│  │  (Partner A      │──►│  (SAP + RKG Sync) │◄──│  (Partner B   │  │
│  │   Private        │   └────────┬──────────┘   │   Private     │  │
│  │   Counselor)     │            │               │   Counselor)  │  │
│  └──────────────────┘            ▼               └───────────────┘  │
│         │                ┌───────────────┐               │          │
│    [Private pgvector]    │  Agent R      │    [Private pgvector]    │
│    [Encrypted per-user]  │  (Relationship│    [Encrypted per-user]  │
│                          │   Counselor)  │                          │
│                          └───────┬───────┘                          │
│                                  │                                  │
│                    ┌─────────────▼──────────────┐                  │
│                    │  Relational Knowledge Graph │                  │
│                    │  (Neo4j RKG)                │                  │
│                    │  Abstracted patterns only   │                  │
│                    └────────────────────────────┘                   │
└─────────────────────────────────────────────────────────────────────┘
```

## Privacy Model (3 Layers)

| Layer | What Lives Here | Who Can Read |
|-------|----------------|--------------|
| **Private Store** | Raw messages, emotional disclosures, full history | That partner's agent only |
| **Pattern Synthesis** | Abstracted themes, intensities — no quotes, no specifics | Privacy Mediator only |
| **RKG** | Relational-level insights (e.g., "withdraw-pursue pattern active") | Agent R, both partners |

The Privacy Firewall enforces **one-way abstraction** — raw content never flows outward. The Signal Abstraction Protocol (SAP) ensures no reconstruction is possible from what enters the shared layer.

---

## Agents

### Agent A / Agent B — Private Counselors
- Fully isolated context per partner
- EFT-informed, warm, present-focused counseling
- LangGraph graph: `retrieve_memory → generate_response → crisis_check → store_memory`
- Memory backed by pgvector (per-user encrypted namespace)

### Agent R — Relationship Counselor
- Operates **only** from abstracted RKG data and SAP signals
- Mediates joint sessions as a neutral "third presence"
- Can conduct guided solo sessions using relational context
- Cannot access either partner's private history

---

## Session Types

| Mode | Participants | Agent |
|------|-------------|-------|
| Solo A / Solo B | Private partner session | Agent A or B |
| Guided | Partner + relational context | Agent R |
| Joint | Both partners, mediated | Agent R |
| Insight Sync | Background | Privacy Mediator → RKG |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11+, FastAPI |
| Agent Framework | LangGraph 0.2+ |
| LLM | Anthropic Claude (`claude-sonnet-4-6`) |
| Private Memory | PostgreSQL + pgvector (per-user namespaces) |
| Relational Graph | Neo4j 5.x |
| Cache / Sessions | Redis |
| Auth | JWT + PBKDF2 per-user key derivation |
| Frontend | Expo (React Native Web) — iOS, Android, Web |
| Infra | Docker Compose |

---

## Project Structure

```
trinitycounselor/
├── prototype/          # Phase 0 reference implementation (in-memory, direct API calls)
├── backend/            # Production backend (FastAPI + LangGraph)
│   ├── app/
│   │   ├── agents/     # LangGraph agent graphs + prompts
│   │   ├── api/        # FastAPI route handlers (v1)
│   │   ├── auth/       # JWT + encryption stubs
│   │   ├── core/       # Logging, exceptions
│   │   ├── memory/     # pgvector conversation store
│   │   ├── privacy/    # Privacy Mediator + SAP
│   │   └── rkg/        # Neo4j client + schema + queries
│   └── alembic/        # DB migrations
├── frontend/           # Expo React Native Web app
└── infra/              # Docker Compose + Neo4j init schema
```

---

## Quickstart

### Prerequisites
- Docker & Docker Compose
- Python 3.11+
- Node.js 18+ (for frontend)

### 1. Start infrastructure

```bash
docker-compose -f infra/docker-compose.yml up -d
```

### 2. Configure environment

```bash
cp backend/.env.example backend/.env
# Edit backend/.env — add ANTHROPIC_API_KEY at minimum
```

### 3. Run migrations

```bash
cd backend
pip install -e ".[dev]"
alembic upgrade head
```

### 4. Start backend

```bash
uvicorn app.main:app --reload --port 8000
```

### 5. Start frontend

```bash
cd frontend
npm install
npx expo start --web
```

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Liveness check |
| `POST` | `/v1/relationships` | Create a relationship + initialize RKG |
| `GET` | `/v1/relationships/{id}/model` | Current relational model from RKG |
| `POST` | `/v1/relationships/{id}/sync` | Trigger SAP → RKG insight sync |
| `POST` | `/v1/agent-a/chat` | Partner A private session |
| `GET` | `/v1/agent-a/history` | Partner A session history |
| `POST` | `/v1/agent-b/chat` | Partner B private session |
| `GET` | `/v1/agent-b/history` | Partner B session history |
| `POST` | `/v1/agent-r/chat` | Guided relational session |
| `POST` | `/v1/agent-r/joint` | Joint mediated session |

---

## RKG Schema (Neo4j)

Core node types and their relationships:

```
(Person)-[:PARTNER_IN]->(Relationship)
(Relationship)-[:HAS_PATTERN]->(RelationalPattern)
(RelationalPattern)-[:INVOLVES_NEED]->(NeedCluster)
(Relationship)-[:HAS_EVENT]->(Event)
(Event)-[:TAGGED_WITH]->(TherapyFrameInsight)
(RelationalPattern)-[:TAGGED_WITH]->(TherapyFrameInsight)
```

---

## Ethics & Safety

- **Relationship-first**: The system serves the relationship, not engagement metrics
- **Continuous consent**: Partners control what enters shared context
- **Crisis protocol**: Active keyword + LLM-based crisis detection with immediate escalation to human resources (988, Crisis Text Line)
- **No weaponization**: Agent R cannot be used to surveil a partner
- **Privacy by design**: The privacy boundary is architectural, not policy-level

See `ARCHITECTURE.md` for the full system design including risks, ethics framework, and roadmap.
