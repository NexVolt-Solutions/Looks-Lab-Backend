from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager

from app.api.v1.api_router import router
from app.core import logging, database
from app.core.config import settings
from app.core.security import SecurityHeadersMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    logging.logger.info("Starting Looks Lab API...")
    database.init_db()

    yield

    # Shutdown logic
    logging.logger.info("Shutting down Looks Lab API...")
    database.close_db()


app = FastAPI(
    title="Looks Lab API",
    version="1.0.0",
    description="Backend API for Looks Lab powered by FastAPI",
    contact={"name": "Looks Lab Team", "email": "support@looks-lab.com"},
    lifespan=lifespan,
)

# Request logging
if settings.ENABLE_REQUEST_LOGGING:
    @app.middleware("http")
    async def request_logging_middleware(request, call_next):
        logging.logger.info("%s %s", request.method, request.url.path)
        return await call_next(request)

# CORS
cors_origins = settings.cors_origins_list
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins if cors_origins else (["*"] if not settings.is_production else []),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Trusted Host Middleware
trusted_hosts = settings.trusted_hosts_list
if trusted_hosts:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=trusted_hosts)

# Security headers
if settings.ENABLE_SECURITY_HEADERS:
    app.add_middleware(SecurityHeadersMiddleware)

# Routers
app.include_router(router)

