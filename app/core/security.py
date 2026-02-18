"""
Security headers middleware.
Adds security headers to all responses to protect against common attacks.
"""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.config import settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Adds security headers to every response."""

    async def dispatch(self, request: Request, call_next) -> Response:
        response: Response = await call_next(request)

        if not settings.ENABLE_SECURITY_HEADERS:
            return response

        # Skip security headers for Swagger UI and API docs
        if request.url.path in ["/docs", "/redoc", "/openapi.json"]:
            return response

        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("X-XSS-Protection", "0")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")

        response.headers.setdefault(
            "Content-Security-Policy",
            "; ".join([
                "default-src 'self'",
                "img-src 'self' data: https:",
                "script-src 'self'",
                "style-src 'self' 'unsafe-inline'",
                "connect-src 'self' https:",
                "frame-ancestors 'none'",
                "base-uri 'self'",
                "form-action 'self'",
            ])
        )

        response.headers.setdefault(
            "Permissions-Policy",
            ", ".join([
                "camera=(self)",
                "microphone=()",
                "geolocation=()",
                "payment=()",
                "usb=()",
                "gyroscope=()",
                "accelerometer=()",
            ])
        )

        if settings.is_production:
            response.headers.setdefault(
                "Strict-Transport-Security",
                "max-age=31536000; includeSubDomains; preload"
            )

        return response

