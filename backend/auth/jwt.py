"""
JWT issuance and verification.

Tokens carry: sub (user_id), email, exp.
"""
import uuid
from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt
from pydantic import BaseModel

from backend.config import settings


class TokenPayload(BaseModel):
    sub: str          # user_id (UUID as string)
    email: str
    exp: datetime


class TokenPair(BaseModel):
    access_token: str
    token_type: str = "bearer"


def create_access_token(user_id: uuid.UUID, email: str) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {
        "sub": str(user_id),
        "email": email,
        "exp": expire,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> TokenPayload:
    """Raises JWTError on invalid/expired tokens."""
    try:
        raw = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        return TokenPayload(**raw)
    except JWTError:
        raise
