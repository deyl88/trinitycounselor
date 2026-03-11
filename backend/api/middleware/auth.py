"""
JWT authentication middleware / FastAPI dependency.

Extracts and validates the Bearer token from the Authorization header,
resolves the User from the database, and injects it into route handlers.

Usage:
    @router.post("/chat")
    async def chat(
        body: ChatRequest,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_session),
    ): ...
"""
import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.jwt import decode_access_token
from backend.db.postgres import get_session
from backend.models.user import User

bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_session),
) -> User:
    """
    FastAPI dependency — validates JWT and returns the authenticated User.
    Raises HTTP 401 on invalid/expired tokens.
    Raises HTTP 404 if the user no longer exists.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(credentials.credentials)
        user_id = uuid.UUID(payload.sub)
    except (JWTError, ValueError):
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    return user
