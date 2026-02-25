"""
Main API router.
Includes all route modules and health check.
"""
from fastapi import APIRouter
from datetime import datetime, timezone
from sqlalchemy import text

from app.core.database import async_engine
from app.api.v1.routes import (
    auth,
    users,
    image,
    insights,
    subscription,
    onboarding,
    domain,
    workout,
    diet,
    legal,
    iap,  # ← ADDED: In-App Purchase routes
)

router = APIRouter()

# ── Authentication ────────────────────────────────────────────────
router.include_router(
    auth.router,
    prefix="/api/v1/auth",
    tags=["Authentication"]
)

# ── Users ─────────────────────────────────────────────────────────
router.include_router(
    users.router,
    prefix="/api/v1/users",
    tags=["Users"]
)

# ── Onboarding ────────────────────────────────────────────────────
router.include_router(
    onboarding.router,
    prefix="/api/v1/onboarding",
    tags=["Onboarding"]
)

# ── Subscriptions ─────────────────────────────────────────────────
router.include_router(
    subscription.router,
    prefix="/api/v1/subscriptions",
    tags=["Subscriptions"]
)

# ── Generic Domain Routes ─────────────────────────────────────────

router.include_router(
    domain.router,
    prefix="/api/v1/domains",
    tags=["Domains"]
)

# ── Workout AI ────────────────────────────────────────────────────
# AI-powered workout plan generation
router.include_router(
    workout.router,
    prefix="/api/v1/domains/workout",
    tags=["Workout"]
)

# ── Diet AI ───────────────────────────────────────────────────────
# AI-powered meal plan generation
router.include_router(
    diet.router,
    prefix="/api/v1/domains/diet",
    tags=["Diet"]
)

# ── Images ────────────────────────────────────────────────────────
router.include_router(
    image.router,
    prefix="/api/v1/images",
    tags=["Images"]
)

# ── Insights ──────────────────────────────────────────────────────
router.include_router(
    insights.router,
    prefix="/api/v1/insights",
    tags=["Insights"]
)

# ── Legal ─────────────────────────────────────────────────────────
router.include_router(
    legal.router,
    prefix="/api/v1/legal",
    tags=["Legal"]
)

# ── In-App Purchase ───────────────────────────────────────────────
router.include_router(
    iap.router,
    prefix="/api/v1/iap",
    tags=["In-App Purchases"]
)


# ── Health Check ──────────────────────────────────────────────────

async def health_check():
    """
    Health check endpoint for monitoring and load balancers.

    Checks:
    - Database connectivity
    - API responsiveness

    Returns:
        dict: Health status with timestamp and database connection state
    """
    db_ok = False
    try:
        async with async_engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
            await conn.commit()
        db_ok = True
    except Exception as e:
        from app.core.logging import logger
        logger.error(f"Health check failed: {e}")
        db_ok = False

    return {
        "status": "ok" if db_ok else "degraded",
        "service": "Looks Lab API",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "database": "connected" if db_ok else "disconnected",
    }
    
    