from __future__ import annotations

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Lightweight security headers middleware.
    Keep this conservative so it doesn't break mobile/web clients unexpectedly.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        response: Response = await call_next(request)

        # Prevent content-type sniffing
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        # Prevent clickjacking
        response.headers.setdefault("X-Frame-Options", "DENY")
        # Basic XSS protection (legacy; harmless)
        response.headers.setdefault("X-XSS-Protection", "0")
        # Referrer privacy
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        # HSTS only makes sense behind HTTPS (terminate TLS at LB). Enable anyway; browsers ignore over http.
        response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")

        return response


