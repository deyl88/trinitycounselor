"""JWT token creation and verification.

Status: STUB — interfaces are fully defined, implementation is wired.
The next step (not in this scaffold) is a users table + /auth/register
and /auth/login endpoints that issue tokens from real DB records.

All agent endpoints depend on `verify_token` via the `CurrentUser` dep.
"""

from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from pydantic import BaseModel

from app.config import get_settings
from app.core.exceptions import AuthError, TokenExpiredError


class TokenPayload(BaseModel):
    """Decoded JWT payload carried through request context."""

    sub: str                 # user_id (UUID string)
    partner_tag: str         # "partner_a" | "partner_b" — drives namespace isolation
    relationship_id: str     # which relationship this user belongs to
    exp: int                 # unix timestamp
    iat: int                 # issued-at unix timestamp


def create_access_token(
    user_id: str,
    partner_tag: str,
    relationship_id: str,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a signed JWT access token for a Trinity user.

    Args:
        user_id: UUID of the authenticated user.
        partner_tag: "partner_a" or "partner_b" — used to route to the
            correct agent and enforce namespace isolation in pgvector.
        relationship_id: The relationship this user is a member of.
        expires_delta: Custom expiry. Defaults to settings value.

    Returns:
        Signed JWT string.
    """
    settings = get_settings()
    now = datetime.now(UTC)
    expire = now + (expires_delta or timedelta(minutes=settings.jwt_access_token_expire_minutes))

    payload: dict[str, Any] = {
        "sub": user_id,
        "partner_tag": partner_tag,
        "relationship_id": relationship_id,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }

    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def verify_token(token: str) -> TokenPayload:
    """Decode and verify a JWT access token.

    Args:
        token: Raw JWT string from the Authorization header.

    Returns:
        Decoded `TokenPayload`.

    Raises:
        TokenExpiredError: If the token's `exp` claim is in the past.
        AuthError: For any other JWT invalidity (bad signature, malformed, etc.).
    """
    settings = get_settings()
    try:
        raw = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return TokenPayload(**raw)
    except jwt.ExpiredSignatureError as exc:
        raise TokenExpiredError("Access token has expired. Please re-authenticate.") from exc
    except JWTError as exc:
        raise AuthError(f"Invalid token: {exc}") from exc
