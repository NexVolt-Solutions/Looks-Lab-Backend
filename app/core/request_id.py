"""
Request ID tracking middleware for request correlation.
"""
import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.logging import logger


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware that adds a unique request ID to each request for tracing.
    The request ID is added to:
    - Request state (accessible via request.state.request_id)
    - Response headers (X-Request-ID)
    - Log messages
    """
    
    async def dispatch(self, request: Request, call_next) -> Response:
        # Generate or use existing request ID
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Log request with request ID
        logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={"request_id": request_id}
        )
        
        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            
            # Log response with request ID
            logger.info(
                f"Request completed: {request.method} {request.url.path} - {response.status_code}",
                extra={"request_id": request_id}
            )
            
            return response
        except Exception as e:
            # Log error with request ID
            logger.error(
                f"Request failed: {request.method} {request.url.path} - {str(e)}",
                extra={"request_id": request_id},
                exc_info=True
            )
            raise
