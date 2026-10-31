"""Rate limiting for FastAPI.

Only per-endpoint @limiter.limit() applies.
No global middleware/default limits — heavy endpoints have explicit limits.
Disabled in local mode (single user).
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from genome_studio.auth.modes import resolve_mode


def _limiter_enabled() -> bool:
    """Rate limiting only active in multi mode."""
    return resolve_mode().value != "local"


limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="memory://",
    enabled=_limiter_enabled(),
    headers_enabled=False,  # True requires response: Response in every endpoint
)


def _rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Custom 429 response with Retry-After."""
    return JSONResponse(
        status_code=429,
        content={
            "detail": "Rate limit exceeded. Please slow down.",
            "limit": str(exc.detail) if exc.detail else "unknown",
        },
        headers={"Retry-After": "60"},
    )


def setup_rate_limiting(app: FastAPI) -> None:
    """Wire limiter and exception handler. No middleware."""
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_handler)  # type: ignore[arg-type]
