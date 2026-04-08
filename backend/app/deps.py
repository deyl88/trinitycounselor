"""FastAPI dependency injection providers.

All route handlers should inject resources via these dependencies rather
than importing singletons directly. This makes testing straightforward —
override deps in conftest.py with test doubles.
"""

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt import TokenPayload, verify_token
from app.config import Settings, get_settings
from app.core.exceptions import AuthError
from app.db.session import get_async_session
from app.rkg.neo4j_client import AsyncDriver, get_driver

_bearer = HTTPBearer(auto_error=False)


# ── Settings ──────────────────────────────────────────────────────────────────


SettingsDep = Annotated[Settings, Depends(get_settings)]


# ── Database ──────────────────────────────────────────────────────────────────


async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield a scoped async SQLAlchemy session."""
    async for session in get_async_session():
        yield session


DBSession = Annotated[AsyncSession, Depends(db_session)]


# ── Neo4j ─────────────────────────────────────────────────────────────────────


async def neo4j_driver() -> AsyncDriver:
    """Return the shared async Neo4j driver."""
    return get_driver()


Neo4jDriver = Annotated[AsyncDriver, Depends(neo4j_driver)]


# ── Auth ──────────────────────────────────────────────────────────────────────


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> TokenPayload:
    """Verify the Bearer JWT and return the decoded payload.

    Raises HTTP 401 if the token is missing, expired, or invalid.
    This dependency is intentionally strict — all agent endpoints require auth.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        return verify_token(credentials.credentials)
    except AuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=exc.message,
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


CurrentUser = Annotated[TokenPayload, Depends(get_current_user)]
