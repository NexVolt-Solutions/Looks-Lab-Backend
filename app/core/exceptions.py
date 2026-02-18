"""
Global exception handlers for consistent error responses.
"""
from fastapi import FastAPI, Request, status, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from app.core.config import settings
from app.core.logging import logger
from app.ai.gemini_client import GeminiError, GeminiTimeoutError, GeminiRateLimitError


# ── Helpers ───────────────────────────────────────────────────────

def _request_context(request: Request) -> str:
    """ Added: include endpoint info in all logs for easier debugging."""
    return f"[{request.method} {request.url.path}]"


# ── Handlers ──────────────────────────────────────────────────────

async def http_exception_handler(
    request: Request,
    exc: HTTPException
) -> JSONResponse:
    """
     Added: Handle FastAPI HTTPExceptions (404, 403, 401 etc.)
    Ensures ALL errors return consistent JSON format.
    """
    logger.warning(
        f"{_request_context(request)} "
        f"HTTP {exc.status_code}: {exc.detail}"
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "status_code": exc.status_code,
        },
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    """
    Handle Pydantic validation errors (422).
    Cleans up error format before sending to client.
    """
    #  Added: clean up errors — remove internal field paths
    errors = []
    for error in exc.errors():
        errors.append({
            "field": " → ".join(str(loc) for loc in error.get("loc", [])),
            "message": error.get("msg", "Invalid value"),
            "type": error.get("type", "")
        })

    logger.warning(
        f"{_request_context(request)} "
        f"Validation error: {len(errors)} field(s) invalid"
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error",
            "errors": errors,
        },
    )


async def integrity_error_handler(
    request: Request,
    exc: IntegrityError
) -> JSONResponse:
    """
    Handle database integrity violations (409).
    Detects common causes like duplicate entries.
    """
    error_str = str(exc.orig).lower() if exc.orig else str(exc).lower()

    #  Added: detect common integrity error causes
    if "unique" in error_str or "duplicate" in error_str:
        if "email" in error_str:
            message = "An account with this email already exists."
        elif "user_id" in error_str:
            message = "You already have an active record of this type."
        else:
            message = "A duplicate entry already exists."
    elif "foreign key" in error_str or "fk" in error_str:
        message = "Referenced record does not exist."
    elif "not null" in error_str:
        message = "A required field is missing."
    else:
        message = "The request conflicts with existing data."

    logger.warning(
        f"{_request_context(request)} "
        f"Integrity error: {type(exc).__name__}"
    )

    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "detail": "Data conflict",
            "message": message,
        },
    )


async def sqlalchemy_exception_handler(
    request: Request,
    exc: SQLAlchemyError
) -> JSONResponse:
    """
    Handle general SQLAlchemy database errors (500).
    """
    logger.error(
        f"{_request_context(request)} "
        f"Database error: {type(exc).__name__}",
        exc_info=settings.is_development
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Database error",
            "message": "An internal error occurred. Please try again later.",
        },
    )


async def gemini_timeout_handler(
    request: Request,
    exc: GeminiTimeoutError
) -> JSONResponse:
    """
     Added: Handle Gemini AI timeout errors (504).
    """
    logger.warning(
        f"{_request_context(request)} "
        f"Gemini timeout: {str(exc)}"
    )

    return JSONResponse(
        status_code=status.HTTP_504_GATEWAY_TIMEOUT,
        content={
            "detail": "AI timeout",
            "message": "AI analysis timed out. Please try again.",
        },
    )


async def gemini_rate_limit_handler(
    request: Request,
    exc: GeminiRateLimitError
) -> JSONResponse:
    """
     Added: Handle Gemini AI rate limit errors (429).
    """
    logger.warning(
        f"{_request_context(request)} "
        f"Gemini rate limit hit"
    )

    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "detail": "AI rate limit",
            "message": "AI service is busy. Please try again in a moment.",
        },
    )


async def gemini_error_handler(
    request: Request,
    exc: GeminiError
) -> JSONResponse:
    """
     Added: Handle general Gemini AI errors (503).
    """
    logger.error(
        f"{_request_context(request)} "
        f"Gemini error: {str(exc)}",
        exc_info=settings.is_development
    )

    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "detail": "AI unavailable",
            "message": "AI analysis service is temporarily unavailable. Please try again later.",
        },
    )


async def general_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """
    Catch-all handler for unexpected errors (500).
    """
    logger.error(
        f"{_request_context(request)} "
        f"Unexpected error: {type(exc).__name__}: {str(exc)}",
        exc_info=settings.is_development
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "message": "An unexpected error occurred. Please try again later.",
        },
    )


# ── Registration ──────────────────────────────────────────────────

def setup_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers with the FastAPI app."""


    app.add_exception_handler(GeminiTimeoutError, gemini_timeout_handler)
    app.add_exception_handler(GeminiRateLimitError, gemini_rate_limit_handler)
    app.add_exception_handler(GeminiError, gemini_error_handler)
    app.add_exception_handler(IntegrityError, integrity_error_handler)
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)

