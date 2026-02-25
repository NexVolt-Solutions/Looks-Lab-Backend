"""
Subscription routes.
Handles subscription creation, retrieval, cancellation, and plan information.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.models.user import User
from app.schemas.subscription import (
    SubscriptionCreate,
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
    """
    Get all available subscription plans with features and pricing.

    Returns:
        List of subscription plans with their details, features, and pricing.

    Note:
        - Plans are dynamically generated using utility functions
        - Prices are in USD
        - The 'monthly' plan is marked as most popular
    """
    # Define plan metadata (id, type, interval, popularity)
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

    # Build plan objects using utility functions
    plans = []
    for metadata in plans_metadata:
        plan_type = metadata["type"]

        plan = {
            "id": metadata["id"],
            "type": plan_type,
            "name": metadata["name"],
            "price": get_plan_price(plan_type),
            "currency": "USD",
            "interval": metadata["interval"],
            "interval_count": 1,
            "features": get_plan_features(plan_type),
            "description": metadata["description"],
            "duration_days": get_plan_duration_days(plan_type),
            "is_popular": metadata["is_popular"],
            "savings_percent": calculate_savings_percent(plan_type)
        }

        plans.append(plan)

    return plans


@router.post("/", response_model=SubscriptionOut)
async def create_subscription(
        payload: SubscriptionCreate,
        db: AsyncSession = Depends(get_async_db),
        current_user: User = Depends(get_current_user),
):
    """
    Create a new subscription for the current user.

    Args:
        payload: Subscription creation data (plan type, status, payment_id)
        db: Database session
        current_user: Authenticated user from JWT token

    Returns:
        Created subscription details

    Raises:
        HTTPException: If user already has an active subscription
    """
    subscription_service = SubscriptionService(db)

    # Override user_id with current authenticated user
    payload.user_id = current_user.id

    # Service layer already handles duplicate subscription check
    return await subscription_service.create_subscription(payload)


@router.get("/me", response_model=SubscriptionOut)
async def get_my_subscription(
        db: AsyncSession = Depends(get_async_db),
        current_user: User = Depends(get_current_user),
):
    """
    Get the current user's subscription details.

    Args:
        db: Database session
        current_user: Authenticated user from JWT token

    Returns:
        User's subscription details including plan, status, and dates

    Raises:
        HTTPException: If user has no subscription
    """
    subscription_service = SubscriptionService(db)
    return await subscription_service.get_user_subscription(current_user.id)


@router.get("/{subscription_id}", response_model=SubscriptionOut)
async def get_subscription_by_id(
        subscription_id: int,
        db: AsyncSession = Depends(get_async_db),
        current_user: User = Depends(get_current_user),
):
    """
    Get a specific subscription by ID.

    Args:
        subscription_id: The subscription ID to retrieve
        db: Database session
        current_user: Authenticated user from JWT token

    Returns:
        Subscription details

    Raises:
        HTTPException: If subscription not found or doesn't belong to user
    """
    subscription_service = SubscriptionService(db)
    subscription = await subscription_service.get_subscription_by_id(subscription_id)

    # Ensure user can only access their own subscription
    if subscription.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this subscription"
        )

    return subscription


@router.patch("/{subscription_id}/cancel", response_model=SubscriptionOut)
async def cancel_subscription(
        subscription_id: int,
        db: AsyncSession = Depends(get_async_db),
        current_user: User = Depends(get_current_user),
):
    """
    Cancel a subscription.

    Args:
        subscription_id: The subscription ID to cancel
        db: Database session
        current_user: Authenticated user from JWT token

    Returns:
        Updated subscription with 'cancelled' status

    Raises:
        HTTPException: If subscription not found, doesn't belong to user,
                      or is already cancelled/expired
    """
    subscription_service = SubscriptionService(db)
    return await subscription_service.cancel_subscription(subscription_id, current_user.id)


@router.patch("/{subscription_id}/reactivate", response_model=SubscriptionOut)
async def reactivate_subscription(
        subscription_id: int,
        db: AsyncSession = Depends(get_async_db),
        current_user: User = Depends(get_current_user),
):
    """
    Reactivate a cancelled subscription (if not expired yet).

    Args:
        subscription_id: The subscription ID to reactivate
        db: Database session
        current_user: Authenticated user from JWT token

    Returns:
        Updated subscription with 'active' status

    Raises:
        HTTPException: If subscription not found, doesn't belong to user,
                      is not cancelled, or has expired
    """
    subscription_service = SubscriptionService(db)
    return await subscription_service.reactivate_subscription(subscription_id, current_user.id)


@router.get("/me/status", response_model=SubscriptionStatusResponse)
async def check_subscription_status(
        db: AsyncSession = Depends(get_async_db),
        current_user: User = Depends(get_current_user),
):
    """
    Check if current user has an active subscription.

    Args:
        db: Database session
        current_user: Authenticated user from JWT token

    Returns:
        Object with subscription status and access information
    """
    subscription_service = SubscriptionService(db)

    return await subscription_service.get_subscription_status(current_user.id)
