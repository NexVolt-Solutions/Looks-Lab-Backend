"""
Rate limiting middleware using slowapi.
"""
try:
    from slowapi import Limiter  # type: ignore
    from slowapi.util import get_remote_address  # type: ignore
    SLOWAPI_AVAILABLE = True
except ImportError:
    SLOWAPI_AVAILABLE = False
    # Create dummy classes if slowapi is not installed
    class Limiter:  # type: ignore
        def __init__(self, *args, **kwargs):
            pass

from fastapi import Request, status
from fastapi.responses import JSONResponse

from app.core.config import settings

# Initialize limiter only if slowapi is available
if SLOWAPI_AVAILABLE:
    limiter = Limiter(key_func=get_remote_address)
else:
    limiter = None


def rate_limit_exceeded_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Custom exception handler for rate limit exceeded errors.
    
    Returns a 429 Too Many Requests response with appropriate headers.
    """
    response = JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "detail": "Rate limit exceeded",
            "message": "Too many requests. Please try again later.",
        },
    )
    # Add Retry-After header if available
    if hasattr(exc, "retry_after"):
        response.headers["Retry-After"] = str(exc.retry_after)
    return response


def create_rate_limit_middleware(app):
    """
    Configure rate limiting for the FastAPI app.
    
    This sets up the rate limiter in the app state and configures
    the exception handler for rate limit exceeded errors.
    
    To use rate limiting on specific routes, add the decorator:
        @limiter.limit(get_rate_limit())
        def my_route(request: Request):
            ...
    
    Args:
        app: FastAPI application instance
        
    Returns:
        Limiter instance for use in route decorators, or None if slowapi not installed
    """
    if not SLOWAPI_AVAILABLE:
        from app.core.logging import logger
        logger.warning("slowapi not installed - rate limiting disabled. Install with: pip install slowapi")
        return None
    
    app.state.limiter = limiter
    
    # Register exception handler for rate limit errors
    try:
        from slowapi.errors import RateLimitExceeded  # type: ignore
        app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
    except ImportError:
        # If slowapi.errors doesn't exist in this version, that's okay
        # The limiter will still work, just without a custom exception handler
        pass
    
    return limiter


def get_rate_limit() -> str:
    """
    Get rate limit string for use in route decorators.
    
    Returns:
        Rate limit string in format "{limit}/minute" based on settings
    """
    return f"{settings.RATE_LIMIT_PER_MINUTE}/minute"
