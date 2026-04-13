"""Async Neo4j driver singleton for the Relational Knowledge Graph.

The RKG stores only abstracted relational patterns — never raw private content.
All writes to Neo4j flow through the Privacy Mediator after SAP extraction.

Usage::

    from app.rkg.neo4j_client import get_driver

    driver = get_driver()
    async with driver.session(database="neo4j") as session:
        result = await session.run("MATCH (r:Relationship {id: $id}) RETURN r", id=rel_id)
        record = await result.single()
"""

from __future__ import annotations

import contextlib
from typing import Any

from neo4j import AsyncDriver, AsyncGraphDatabase
from neo4j.exceptions import ServiceUnavailable

from app.config import get_settings
from app.core.exceptions import RKGConnectionError
from app.core.logging import get_logger

logger = get_logger(__name__)

_driver: AsyncDriver | None = None


def get_driver() -> AsyncDriver:
    """Return the module-level async Neo4j driver.

    The driver is created lazily on first call and reused thereafter.
    Call `close_driver()` during application shutdown.
    """
    global _driver
    if _driver is None:
        settings = get_settings()
        _driver = AsyncGraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
            max_connection_pool_size=50,
        )
        logger.info("neo4j_driver_created", uri=settings.neo4j_uri)
    return _driver


async def close_driver() -> None:
    """Close the driver and release all pooled connections.

    Call this in the FastAPI lifespan shutdown handler.
    """
    global _driver
    if _driver is not None:
        await _driver.close()
        _driver = None
        logger.info("neo4j_driver_closed")


async def verify_connectivity() -> None:
    """Ping Neo4j to confirm the connection is healthy.

    Raises:
        RKGConnectionError: If Neo4j is unreachable.
    """
    driver = get_driver()
    try:
        await driver.verify_connectivity()
        logger.info("neo4j_connectivity_ok")
    except ServiceUnavailable as exc:
        raise RKGConnectionError(
            f"Cannot connect to Neo4j at {get_settings().neo4j_uri}: {exc}"
        ) from exc


@contextlib.asynccontextmanager
async def rkg_session(**kwargs: Any):
    """Async context manager yielding a Neo4j async session.

    Usage::

        async with rkg_session() as session:
            await session.run(...)
    """
    driver = get_driver()
    async with driver.session(**kwargs) as session:
        yield session
