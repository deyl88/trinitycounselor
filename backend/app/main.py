"""Trinity Backend — FastAPI application entry point.

Startup sequence (lifespan):
  1. Configure structured logging
  2. Verify Neo4j connectivity + run schema initialization
  3. Register exception handlers
  4. Mount routers

Shutdown sequence:
  1. Close Neo4j driver connection pool
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import router as health_router
from app.api.v1.router import router as v1_router
from app.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging, get_logger
from app.rkg.neo4j_client import close_driver, verify_connectivity
from app.rkg.schema import init_schema

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """FastAPI lifespan: startup and shutdown logic."""
    settings = get_settings()

    # ── Startup ───────────────────────────────────────────────────────────────
    configure_logging()
    logger.info("trinity_startup", env=settings.app_env)

    try:
        await verify_connectivity()
        await init_schema()
        logger.info("rkg_ready")
    except Exception as exc:
        logger.error("rkg_startup_failed", error=str(exc))
        # Don't hard-fail startup if Neo4j is unavailable in dev
        if settings.app_env == "production":
            raise

    logger.info("trinity_ready", env=settings.app_env)

    yield  # Application is running

    # ── Shutdown ──────────────────────────────────────────────────────────────
    logger.info("trinity_shutdown")
    await close_driver()


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Trinity Counselor API",
        description=(
            "Multi-agent AI relationship counseling system. "
            "Three agents — Agent A, Agent B, and the Relationship Counselor (Agent R) — "
            "share abstracted relational insight while preserving strict privacy boundaries."
        ),
        version="0.1.0",
        docs_url="/docs" if settings.app_env != "production" else None,
        redoc_url="/redoc" if settings.app_env != "production" else None,
        lifespan=lifespan,
    )

    # ── CORS ──────────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    # ── Exception handlers ────────────────────────────────────────────────────
    register_exception_handlers(app)

    # ── Routers ───────────────────────────────────────────────────────────────
    app.include_router(health_router)
    app.include_router(v1_router)

    return app


app = create_app()
