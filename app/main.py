from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles

from prometheus_fastapi_instrumentator import Instrumentator

from app.core.config import settings
from app.core.database import init_async_db, close_async_db
from app.core.exceptions import setup_exception_handlers
from app.core.logging import setup_logging, logger
from app.core.rate_limit import setup_rate_limiting
from app.core.request_id import RequestIDMiddleware
from app.core.security import SecurityHeadersMiddleware
from app.api.v1.api_router import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info(f"Starting Looks Lab API — env: {settings.ENV}")

    await init_async_db()

    yield

    await close_async_db()
    logger.info("Looks Lab API shut down")


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

# Request tracing
app.add_middleware(RequestIDMiddleware)

# Security headers
if settings.ENABLE_SECURITY_HEADERS:
    app.add_middleware(SecurityHeadersMiddleware)

# Trusted hosts
if settings.trusted_hosts_list:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.trusted_hosts_list)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-Response-Time"],
)

# Rate limiting
setup_rate_limiting(app)

# Exception handlers
setup_exception_handlers(app)

# Static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# API routes
app.include_router(router)

# Metrics (Prometheus)
Instrumentator().instrument(app).expose(app)

