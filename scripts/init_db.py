#!/usr/bin/env python3
"""
Initialize the PostgreSQL database.

1. Enables the pgvector extension
2. Creates all SQLAlchemy ORM tables
3. Creates LangGraph checkpointer tables (via AsyncPostgresSaver.setup())

Run once on a fresh database:
  python scripts/init_db.py
"""
import asyncio
import sys
from pathlib import Path

# Ensure backend package is importable from the project root
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncpg
from sqlalchemy.ext.asyncio import create_async_engine

from backend.config import settings
from backend.db.postgres import Base

# Import all models so SQLAlchemy registers them before metadata.create_all
from backend.models import user, session, message, pattern  # noqa: F401


async def main() -> None:
    print("🔧 Initialising Trinity database...")

    # Step 1: Enable pgvector extension (must use raw asyncpg — not SQLAlchemy)
    print("  → Enabling pgvector extension...")
    raw_url = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")
    conn = await asyncpg.connect(raw_url)
    try:
        await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        print("  ✓ pgvector extension ready.")
    finally:
        await conn.close()

    # Step 2: Create ORM tables
    print("  → Creating ORM tables...")
    engine = create_async_engine(settings.database_url, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()
    print("  ✓ ORM tables created.")

    # Step 3: Create LangGraph checkpointer tables
    print("  → Creating LangGraph checkpointer tables...")
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
    checkpointer = AsyncPostgresSaver.from_conn_string(settings.postgres_url)
    await checkpointer.setup()
    print("  ✓ Checkpointer tables created.")

    print("\n✅ Database initialisation complete.")


if __name__ == "__main__":
    asyncio.run(main())
