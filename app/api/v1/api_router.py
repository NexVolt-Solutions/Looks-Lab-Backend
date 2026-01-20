from fastapi import APIRouter
from datetime import datetime, timezone

# DB health
from sqlalchemy import text
from app.core.database import engine

# Import all route modules
from app.api.v1.routes import auth, users, image, insights, subscription, onboarding, domain

# Main API router - no prefix here, sub-routers have their own prefixes
router = APIRouter()

# Include routers with centralized prefixes and tags
# Each router has its own tag to organize endpoints in Swagger UI
router.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
router.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
router.include_router(onboarding.router, prefix="/api/v1/onboarding", tags=["Onboarding"])
router.include_router(domain.router, prefix="/api/v1/domains", tags=["Domains"])
router.include_router(image.router, prefix="/api/v1/images", tags=["Images"])
router.include_router(insights.router, prefix="/api/v1/insights", tags=["Insights"])
router.include_router(subscription.router, prefix="/api/v1/subscriptions", tags=["Subscriptions"])


# Health check route (exported for root-level registration)
def health_check():
    """Health check endpoint for monitoring."""
    db_ok = False
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            conn.commit()
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

