"""
Subscription routes.
Handles subscription creation, retrieval, and cancellation.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.models.user import User
from app.schemas.subscription import SubscriptionCreate, SubscriptionOut
from app.services.subscription_service import SubscriptionService
from app.utils.jwt_utils import get_current_user

router = APIRouter()


@router.post("/", response_model=SubscriptionOut)
async def create_subscription(
        payload: SubscriptionCreate,
        db: AsyncSession = Depends(get_async_db),
        current_user: User = Depends(get_current_user),
):
    subscription_service = SubscriptionService(db)

    payload.user_id = current_user.id

    return await subscription_service.create_subscription(payload)


@router.get("/me", response_model=SubscriptionOut)
async def get_my_subscription(
        db: AsyncSession = Depends(get_async_db),
        current_user: User = Depends(get_current_user),
):
    subscription_service = SubscriptionService(db)
    return await subscription_service.get_user_subscription(current_user.id)


@router.patch("/{subscription_id}/cancel", response_model=SubscriptionOut)
async def cancel_subscription(
        subscription_id: int,
        db: AsyncSession = Depends(get_async_db),
        current_user: User = Depends(get_current_user),
):
    subscription_service = SubscriptionService(db)
    return await subscription_service.cancel_subscription(subscription_id, current_user.id)

