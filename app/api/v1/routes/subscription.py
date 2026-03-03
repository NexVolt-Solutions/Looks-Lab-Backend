from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.models.user import User
from app.schemas.subscription import (
    SubscriptionOut,
    SubscriptionPlanOut,
    SubscriptionStatusResponse,
    PlanType,
    SubscriptionInterval
)
from app.services.subscription_service import SubscriptionService
from app.utils.jwt_utils import get_current_user
from app.utils.subscription_utils import (
    get_plan_price,
    get_plan_duration_days,
    get_plan_features,
    calculate_savings_percent
)

router = APIRouter()


@router.get("/plans", response_model=List[SubscriptionPlanOut])
async def get_subscription_plans():
    plans_metadata = [
        {
            "id": "plan_weekly",
            "type": PlanType.weekly,
            "name": "Weekly Plan",
            "interval": SubscriptionInterval.week,
            "description": "Perfect for trying out our services",
            "is_popular": False
        },
        {
            "id": "plan_monthly",
            "type": PlanType.monthly,
            "name": "Monthly Plan",
            "interval": SubscriptionInterval.month,
            "description": "Most popular choice for consistent results",
            "is_popular": True
        },
        {
            "id": "plan_yearly",
            "type": PlanType.yearly,
            "name": "Yearly Plan",
            "interval": SubscriptionInterval.year,
            "description": "Best value for long-term transformation",
            "is_popular": False
        }
    ]

    return [
        {
            "id": m["id"],
            "type": m["type"],
            "name": m["name"],
            "price": get_plan_price(m["type"]),
            "currency": "USD",
            "interval": m["interval"],
            "interval_count": 1,
            "features": get_plan_features(m["type"]),
            "description": m["description"],
            "duration_days": get_plan_duration_days(m["type"]),
            "is_popular": m["is_popular"],
            "savings_percent": calculate_savings_percent(m["type"])
        }
        for m in plans_metadata
    ]


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

