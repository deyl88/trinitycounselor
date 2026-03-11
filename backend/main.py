"""
Trinity Counselor — FastAPI Application Entry Point
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.db.neo4j import close_neo4j_driver, init_neo4j_driver
from backend.db.postgres import close_db, init_db
from backend.api.routes import agent_a, agent_b, agent_r, sessions


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage startup and shutdown of shared resources."""
    await init_db()
    await init_neo4j_driver()

    # Compile LangGraph agents (initialises PostgresSaver checkpointer tables)
    from backend.agents.agent_a import init_agent_a
    from backend.agents.agent_b import init_agent_b
    from backend.agents.agent_r import init_agent_r
    await init_agent_a()
    await init_agent_b()
    await init_agent_r()

    yield
    await close_db()
    await close_neo4j_driver()


app = FastAPI(
    title="Trinity Counselor API",
    description=(
        "Multi-agent AI relationship counseling system. "
        "Three agents — Agent A (private counselor for Partner A), "
        "Agent B (private counselor for Partner B), "
        "Agent R (relationship mediator) — form a unified relational intelligence."
    ),
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# ── CORS ─────────────────────────────────────────────────────────────────────
# Tighten allowed_origins in production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.debug else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(agent_a.router, prefix="/agent-a", tags=["Agent A"])
app.include_router(agent_b.router, prefix="/agent-b", tags=["Agent B"])
app.include_router(agent_r.router, prefix="/agent-r", tags=["Agent R"])
app.include_router(sessions.router, prefix="/sessions", tags=["Sessions"])


@app.get("/health", tags=["Health"])
async def health() -> dict:
    return {"status": "ok", "service": "trinity-counselor"}
