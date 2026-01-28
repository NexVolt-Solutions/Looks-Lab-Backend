"""
Main FastAPI application entry point.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager

from app.api.v1.api_router import router, health_check
from app.core import logging, database
from app.core.config import settings
from app.core.security import SecurityHeadersMiddleware
from app.core.rate_limit import create_rate_limit_middleware
from app.core.exceptions import setup_exception_handlers
from app.core.request_id import RequestIDMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.logger.info("Starting Looks Lab API...")

    try:
        settings.validate_settings()
        logging.logger.info("Configuration validated successfully")
    except ValueError as e:
        logging.logger.error(f"Configuration error: {e}")
        raise

    await database.init_async_db()

    yield

    logging.logger.info("Shutting down Looks Lab API...")
    await database.close_async_db()


app = FastAPI(
    title="Looks Lab API",
    version="1.0.0",
    description="Backend API for Looks Lab powered by FastAPI",
    contact={"name": "Looks Lab Team", "email": "support@looks-lab.com"},
    lifespan=lifespan,
)

app.add_middleware(RequestIDMiddleware)

if settings.ENABLE_REQUEST_LOGGING:
    @app.middleware("http")
    async def request_logging_middleware(request, call_next):
        request_id = getattr(request.state, "request_id", "unknown")
        logging.logger.info(
            "%s %s [Request-ID: %s]",
            request.method,
            request.url.path,
            request_id
        )
        return await call_next(request)

cors_origins = settings.cors_origins_list
if not cors_origins:
    if settings.is_production:
        logging.logger.warning("CORS_ORIGINS not set in production - CORS will be disabled")
        cors_origins = []
    else:
        cors_origins = [
            "http://localhost:3000",
            "http://localhost:8000",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:8000"
        ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

trusted_hosts = settings.trusted_hosts_list
if trusted_hosts:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=trusted_hosts)

if settings.ENABLE_SECURITY_HEADERS:
    app.add_middleware(SecurityHeadersMiddleware)

create_rate_limit_middleware(app)

setup_exception_handlers(app)

app.include_router(router)

app.get("/health", tags=["system"])(health_check)

