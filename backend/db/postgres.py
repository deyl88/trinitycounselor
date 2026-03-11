"""
Async PostgreSQL engine and session factory (SQLAlchemy 2.0).
Used for application data (users, couples, sessions, messages).
"""
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from backend.config import settings

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


class Base(DeclarativeBase):
    """SQLAlchemy declarative base — all ORM models inherit from this."""


async def init_db() -> None:
    global _engine, _session_factory
    _engine = create_async_engine(
        settings.database_url,
        echo=settings.debug,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
    )
    _session_factory = async_sessionmaker(_engine, expire_on_commit=False)

    # Create tables (for dev). In production use Alembic migrations.
    async with _engine.begin() as conn:
        from backend.models import user, session, message, pattern  # noqa: F401 — registers models
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    if _engine:
        await _engine.dispose()


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency — yields a database session."""
    if _session_factory is None:
        raise RuntimeError("Database not initialised. Call init_db() first.")
    async with _session_factory() as session:
        yield session


def get_engine() -> AsyncEngine:
    if _engine is None:
        raise RuntimeError("Database not initialised. Call init_db() first.")
    return _engine
