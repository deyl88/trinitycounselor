"""
Neo4j async driver — manages connection lifecycle.
"""
from neo4j import AsyncDriver, AsyncGraphDatabase

from backend.config import settings

_driver: AsyncDriver | None = None


async def init_neo4j_driver() -> None:
    global _driver
    _driver = AsyncGraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password),
        max_connection_pool_size=50,
    )
    # Verify connectivity at startup
    await _driver.verify_connectivity()


async def close_neo4j_driver() -> None:
    if _driver:
        await _driver.close()


def get_driver() -> AsyncDriver:
    if _driver is None:
        raise RuntimeError("Neo4j driver not initialised. Call init_neo4j_driver() first.")
    return _driver
