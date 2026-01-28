"""
Rate limiting middleware using slowapi.
"""
try:
    from slowapi import Limiter
    from slowapi.util import get_remote_address

    SLOWAPI_AVAILABLE = True
except ImportError:
    SLOWAPI_AVAILABLE = False


    class Limiter:
        def __init__(self, *args, **kwargs):
            pass

from fastapi import Request, status
from fastapi.responses import JSONResponse

from app.core.config import settings

if SLOWAPI_AVAILABLE:
    limiter = Limiter(key_func=get_remote_address)
else:
    limiter = None


def rate_limit_exceeded_handler(request: Request, exc: Exception) -> JSONResponse:
    response = JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "detail": "Rate limit exceeded",
            "message": "Too many requests. Please try again later.",
        },
    )
    if hasattr(exc, "retry_after"):
        response.headers["Retry-After"] = str(exc.retry_after)
    return response


def create_rate_limit_middleware(app):
    if not SLOWAPI_AVAILABLE:
        from app.core.logging import logger
        logger.warning("slowapi not installed - rate limiting disabled. Install with: pip install slowapi")
        return None

    app.state.limiter = limiter

    try:
        from slowapi.errors import RateLimitExceeded
        app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
    except ImportError:
        pass

    return limiter


def get_rate_limit() -> str:
    return f"{settings.RATE_LIMIT_PER_MINUTE}/minute"

