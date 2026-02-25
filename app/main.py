"""
Main FastAPI application entry point.
Looks Lab API — powered by FastAPI.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.api.v1.api_router import router, health_check
from app.core.config import settings
from app.core.database import init_async_db, close_async_db
from app.core.exceptions import setup_exception_handlers
from app.core.logging import setup_logging, logger
from app.core.rate_limit import setup_rate_limiting
from app.core.request_id import RequestIDMiddleware
from app.core.security import SecurityHeadersMiddleware


# ── Lifespan ──────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle."""
    setup_logging()
    logger.info("Starting Looks Lab API...")
    logger.info(f"Environment: {settings.ENV}")

    await init_async_db()
    logger.info("Database connection established")

    yield

    logger.info("Shutting down Looks Lab API...")
    await close_async_db()
    logger.info("Database connection closed")


# ── App Instance ──────────────────────────────────────────────────

app = FastAPI(
    title="Looks Lab API",
    version="1.0.0",
    description="Backend API for Looks Lab — AI-powered personal transformation",
    contact={"name": "Looks Lab Team", "email": "support@looks-lab.com"},
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)



# ── Middleware ────────────────────────────────────────────────────

app.add_middleware(RequestIDMiddleware)

if settings.ENABLE_SECURITY_HEADERS:
    app.add_middleware(SecurityHeadersMiddleware)

trusted_hosts = settings.trusted_hosts_list
if trusted_hosts:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=trusted_hosts)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-Response-Time"],
)


# ── Rate Limiting ─────────────────────────────────────────────────

setup_rate_limiting(app)


# ── Exception Handlers ────────────────────────────────────────────

setup_exception_handlers(app)


# ── Routes ────────────────────────────────────────────────────────

# Include all API routes
app.include_router(router)

# Health check at root level
app.get("/health", tags=["System"])(health_check)

