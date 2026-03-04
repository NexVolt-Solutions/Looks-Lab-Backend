from datetime import datetime, timezone

from fastapi import APIRouter
from sqlalchemy import text

from app.core.database import async_engine
from app.core.logging import logger
from app.api.v1.routes import (
    auth, users, image, insights,
    subscription, onboarding, domain,
    workout, diet, legal, iap,
)

router = APIRouter()

router.include_router(auth.router,         prefix="/api/v1/auth",             tags=["Authentication"])
router.include_router(users.router,        prefix="/api/v1/users",            tags=["Users"])
router.include_router(onboarding.router,   prefix="/api/v1/onboarding",       tags=["Onboarding"])
router.include_router(subscription.router, prefix="/api/v1/subscriptions",    tags=["Subscriptions"])
router.include_router(domain.router,       prefix="/api/v1/domains",          tags=["Domains"])
router.include_router(workout.router,      prefix="/api/v1/domains/workout",  tags=["Workout"])
router.include_router(diet.router,         prefix="/api/v1/domains/diet",     tags=["Diet"])
router.include_router(image.router,        prefix="/api/v1/images",           tags=["Images"])
router.include_router(insights.router,     prefix="/api/v1/insights",         tags=["Insights"])
router.include_router(legal.router,        prefix="/api/v1/legal",            tags=["Legal"])
router.include_router(iap.router,          prefix="/api/v1/iap",              tags=["In-App Purchases"])


async def health_check():
    try:
        async with async_engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        db_ok = True
    except Exception as e:
        logger.error(f"Health check DB error: {e}")
        db_ok = False

    return {
        "status": "ok" if db_ok else "degraded",
        "service": "Looks Lab API",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "database": "connected" if db_ok else "disconnected",
    }

