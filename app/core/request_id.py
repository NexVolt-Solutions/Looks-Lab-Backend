"""
Request ID tracking middleware for request correlation.
"""
import time
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.config import settings
from app.core.logging import logger


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware that:
    - Assigns a unique request ID to every request
    - Tracks request duration
    - Adds X-Request-ID and X-Response-Time headers
    - Logs request/response info based on settings
    """

    async def dispatch(self, request: Request, call_next) -> Response:

        request_id = (
            request.headers.get("X-Request-ID")
            or str(uuid.uuid4())
        )
        request.state.request_id = request_id


        start_time = time.perf_counter()


        if settings.ENABLE_REQUEST_LOGGING:
            logger.info(
                f"→ {request.method} {request.url.path}",
                extra={"request_id": request_id}
            )

        try:
            response = await call_next(request)


            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)


            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time"] = f"{duration_ms}ms"


            if settings.ENABLE_REQUEST_LOGGING:

                level = (
                    logger.warning
                    if duration_ms > 2000        # warn if > 2 seconds
                    else logger.info
                )
                level(
                    f"← {request.method} {request.url.path} "
                    f"[{response.status_code}] {duration_ms}ms",
                    extra={"request_id": request_id}
                )

            return response

        except Exception as e:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

            logger.error(
                f"✗ {request.method} {request.url.path} "
                f"failed after {duration_ms}ms: {type(e).__name__}",
                extra={"request_id": request_id},
                exc_info=settings.is_development
            )
            raise

