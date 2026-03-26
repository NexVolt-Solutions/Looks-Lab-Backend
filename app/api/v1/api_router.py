from fastapi import APIRouter
from app.api.v1.routes import (
    auth, users, image, insights,
    subscription, onboarding, domain,
    workout, diet, legal, iap,
    workout_completion,
)

router = APIRouter()

router.include_router(auth.router,               prefix="/api/v1/auth",            tags=["Authentication"])
router.include_router(users.router,              prefix="/api/v1/users",           tags=["Users"])
router.include_router(onboarding.router,         prefix="/api/v1/onboarding",      tags=["Onboarding"])
router.include_router(subscription.router,       prefix="/api/v1/subscriptions",   tags=["Subscriptions"])
router.include_router(domain.router,             prefix="/api/v1/domains",         tags=["Domains"])
router.include_router(workout.router,            prefix="/api/v1/domains/workout", tags=["Workout"])
router.include_router(workout_completion.router, prefix="/api/v1/domains",         tags=["Workout Completion"])
router.include_router(diet.router,               prefix="/api/v1/domains/diet",    tags=["Diet"])
router.include_router(image.router,              prefix="/api/v1/images",          tags=["Images"])
router.include_router(insights.router,           prefix="/api/v1/insights",        tags=["Insights"])
router.include_router(legal.router,              prefix="/api/v1/legal",           tags=["Legal"])
router.include_router(iap.router,                prefix="/api/v1/iap",             tags=["In-App Purchases"])

