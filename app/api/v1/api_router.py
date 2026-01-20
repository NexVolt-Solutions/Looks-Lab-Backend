from fastapi import APIRouter
from datetime import datetime

# DB health
from sqlalchemy import text
from app.core.database import engine

# Import all route modules
from app.api.v1.routes import auth, users, image, insights, subscription, onboarding, domain

router = APIRouter()

# Include routers with centralized prefixes and tags
router.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
router.include_router(users.router, prefix="/api/v1/users", tags=["users"])
router.include_router(onboarding.router, prefix="/api/v1/onboarding", tags=["onboarding"])
router.include_router(domain.router, prefix="/api/v1/domains", tags=["domains"])
router.include_router(image.router, prefix="/api/v1/images", tags=["images"])
router.include_router(insights.router, prefix="/api/v1/insights", tags=["insights"])
router.include_router(subscription.router, prefix="/api/v1/subscriptions", tags=["subscriptions"])

# Health check route
@router.get("/health", tags=["system"])
def health_check():
    db_ok = False
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False
    return {
        "status": "ok" if db_ok else "degraded",
        "service": "Looks Lab API",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "database": "connected" if db_ok else "disconnected",
    }

