"""
Rate limiting middleware using slowapi.
"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.core.config import settings
from app.core.logging import logger


# ── Limiter Instance ──────────────────────────────────────────────

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{settings.RATE_LIMIT_PER_MINUTE}/minute"]
)


# ── Rate Limit Presets ────────────────────────────────────────────
#  Added: different limits for different endpoint types

class RateLimits:
    """
    Predefined rate limits for different endpoint categories.

    Usage in routes:
        @router.post("/analyze")
        @limiter.limit(RateLimits.AI)
        async def analyze(..., request: Request):
    """
    DEFAULT = f"{settings.RATE_LIMIT_PER_MINUTE}/minute"
    AUTH = "10/minute"
    AI = "10/minute"
    UPLOAD = "20/minute"
    BARCODE = "30/minute"


# ── Handler ───────────────────────────────────────────────────────

def rate_limit_exceeded_handler(
    request: Request,
    exc: RateLimitExceeded
) -> JSONResponse:
    """
    Return 429 response when rate limit is exceeded.
    Includes Retry-After header so client knows when to retry.
    """

    retry_after = getattr(exc, "retry_after", 60)

    logger.warning(
        f"[{request.method} {request.url.path}] "
        f"Rate limit exceeded from {get_remote_address(request)}"
    )

    response = JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "detail": "Rate limit exceeded",
            "message": f"Too many requests. Please try again in {retry_after} seconds.",
            "retry_after": retry_after,
        },
    )


    response.headers["Retry-After"] = str(retry_after)
    response.headers["X-RateLimit-Limit"] = str(settings.RATE_LIMIT_PER_MINUTE)

    return response


# ── Setup ─────────────────────────────────────────────────────────

def setup_rate_limiting(app) -> Limiter:
    """
    Configure rate limiting for the FastAPI app.

    Args:
        app: FastAPI application instance

    Returns:
        Configured Limiter instance
    """
    # Attach limiter to app state — required by slowapi
    app.state.limiter = limiter

    # Register rate limit exceeded handler
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

    logger.info(
        f"Rate limiting enabled | "
        f"default={RateLimits.DEFAULT} | "
        f"auth={RateLimits.AUTH} | "
        f"ai={RateLimits.AI}"
    )

    return limiter

