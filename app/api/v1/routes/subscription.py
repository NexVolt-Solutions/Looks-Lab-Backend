from typing import List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.models.user import User
from app.schemas.subscription import (
    SubscriptionInterval,
    SubscriptionOut,
    SubscriptionPlanOut,
    SubscriptionStatusResponse,
    PlanType,
)
from app.services.subscription_service import SubscriptionService
from app.utils.jwt_utils import get_current_user

router = APIRouter()

_PLANS: List[SubscriptionPlanOut] = [
    SubscriptionPlanOut(
        id="plan_weekly",
        type=PlanType.weekly,
        name="Weekly Plan",
        price=4.99,
        currency="USD",
        interval=SubscriptionInterval.week,
        interval_count=1,
        features=["AI-Powered Analysis", "Expert Transformations", "Priority Post", "Unlimited Consultations"],
        description="Perfect for trying out our services",
        duration_days=7,
        is_popular=False,
        savings_percent=None,
    ),
    SubscriptionPlanOut(
        id="plan_monthly",
        type=PlanType.monthly,
        name="Monthly Plan",
        price=9.99,
        currency="USD",
        interval=SubscriptionInterval.month,
        interval_count=1,
        features=["AI-Powered Analysis", "Expert Transformations", "Priority Post", "Unlimited Consultations", "Weekly Progress Reports"],
        description="Most popular choice for consistent results",
        duration_days=30,
        is_popular=True,
        savings_percent=41,
    ),
    SubscriptionPlanOut(
        id="plan_yearly",
        type=PlanType.yearly,
        name="Yearly Plan",
        price=29.99,
        currency="USD",
        interval=SubscriptionInterval.year,
        interval_count=1,
        features=["AI-Powered Analysis", "Expert Transformations", "Priority Post", "Unlimited Consultations", "Weekly Progress Reports", "Priority Support"],
        description="Best value for long-term transformation",
        duration_days=365,
        is_popular=False,
        savings_percent=75,
    ),
]


@router.get("/plans", response_model=List[SubscriptionPlanOut])
async def get_subscription_plans():
    return _PLANS


@router.get("/me", response_model=SubscriptionOut)
async def get_my_subscription(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    return await SubscriptionService(db).get_user_subscription(current_user.id)


@router.get("/me/status", response_model=SubscriptionStatusResponse)
async def check_subscription_status(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    return await SubscriptionService(db).get_subscription_status(current_user.id)

