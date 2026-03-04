from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.config import settings

_DOCS_PATHS = {"/docs", "/redoc", "/openapi.json"}

_CSP = "; ".join([
    "default-src 'self'",
    "img-src 'self' data: https:",
    "script-src 'self'",
    "style-src 'self' 'unsafe-inline'",
    "connect-src 'self' https:",
    "frame-ancestors 'none'",
    "base-uri 'self'",
    "form-action 'self'",
])

_PERMISSIONS = ", ".join([
    "camera=(self)",
    "microphone=()",
    "geolocation=()",
    "payment=()",
    "usb=()",
    "gyroscope=()",
    "accelerometer=()",
])


class SecurityHeadersMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next) -> Response:
        response: Response = await call_next(request)

        if not settings.ENABLE_SECURITY_HEADERS or request.url.path in _DOCS_PATHS:
            return response

        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("X-XSS-Protection", "0")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Content-Security-Policy", _CSP)
        response.headers.setdefault("Permissions-Policy", _PERMISSIONS)

        if settings.is_production:
            response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains; preload")

        return response

