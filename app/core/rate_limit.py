from fastapi import Request, status
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.core.config import settings
from app.core.logging import logger

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{settings.RATE_LIMIT_PER_MINUTE}/minute"]
)


class RateLimits:
    DEFAULT = f"{settings.RATE_LIMIT_PER_MINUTE}/minute"
    AUTH    = "10/minute"
    AI      = "10/minute"
    UPLOAD  = "20/minute"
    BARCODE = "30/minute"


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    retry_after = getattr(exc, "retry_after", 60)
    logger.warning(f"[{request.method} {request.url.path}] Rate limit exceeded from {get_remote_address(request)}")

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


def setup_rate_limiting(app) -> None:
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

