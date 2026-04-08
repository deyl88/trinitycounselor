"""Trinity exception hierarchy and FastAPI exception handlers."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.logging import get_logger

logger = get_logger(__name__)


# ── Base ──────────────────────────────────────────────────────────────────────


class TrinityError(Exception):
    """Base class for all Trinity application errors."""

    http_status: int = 500
    error_code: str = "internal_error"

    def __init__(self, message: str, **context: object) -> None:
        super().__init__(message)
        self.message = message
        self.context = context


# ── Auth ──────────────────────────────────────────────────────────────────────


class AuthError(TrinityError):
    http_status = 401
    error_code = "auth_error"


class TokenExpiredError(AuthError):
    error_code = "token_expired"


class InsufficientPermissionsError(AuthError):
    http_status = 403
    error_code = "insufficient_permissions"


# ── Privacy ───────────────────────────────────────────────────────────────────


class PrivacyBoundaryViolation(TrinityError):
    """Raised when code attempts to cross the privacy firewall."""

    http_status = 403
    error_code = "privacy_boundary_violation"


class UnauthorizedNamespaceAccess(PrivacyBoundaryViolation):
    """Raised when an agent attempts to access another agent's memory namespace."""

    error_code = "unauthorized_namespace_access"


# ── Memory ────────────────────────────────────────────────────────────────────


class MemoryStoreError(TrinityError):
    error_code = "memory_store_error"


# ── RKG ───────────────────────────────────────────────────────────────────────


class RKGError(TrinityError):
    error_code = "rkg_error"


class RKGConnectionError(RKGError):
    error_code = "rkg_connection_error"


# ── Agent ─────────────────────────────────────────────────────────────────────


class AgentError(TrinityError):
    error_code = "agent_error"


class AgentInvokeError(AgentError):
    error_code = "agent_invoke_error"


# ── Not Found / Validation ────────────────────────────────────────────────────


class NotFoundError(TrinityError):
    http_status = 404
    error_code = "not_found"


class ValidationError(TrinityError):
    http_status = 422
    error_code = "validation_error"


# ── FastAPI handlers ──────────────────────────────────────────────────────────


def _error_response(exc: TrinityError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.http_status,
        content={
            "error": exc.error_code,
            "message": exc.message,
        },
    )


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(TrinityError)
    async def trinity_error_handler(request: Request, exc: TrinityError) -> JSONResponse:
        logger.warning(
            "trinity_error",
            error_code=exc.error_code,
            message=exc.message,
            path=str(request.url),
            **exc.context,
        )
        return _error_response(exc)

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.error(
            "unhandled_exception",
            exc_info=exc,
            path=str(request.url),
        )
        return JSONResponse(
            status_code=500,
            content={"error": "internal_error", "message": "An unexpected error occurred."},
        )
