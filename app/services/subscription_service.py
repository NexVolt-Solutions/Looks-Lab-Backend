"""
Subscription service layer.
Handles subscription operations (create, cancel, check status, reactivate).
"""
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.models.subscription import Subscription, SubscriptionStatus
from app.models.user import User
from app.schemas.subscription import (
    SubscriptionCreate,
    SubscriptionUpdate,
    PlanType
)
from app.utils.subscription_utils import (  # ✅ Import from utils
    calculate_end_date,
    get_plan_price
)
from app.core.logging import logger


class SubscriptionService:
    """Service class for subscription-related operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_subscription(self, payload: SubscriptionCreate) -> Subscription:
        """
        Create a new subscription for a user.

        Args:
            payload: Subscription creation data

        Returns:
            Created subscription object

        Raises:
            HTTPException: If user already has an active subscription
        """
        # ✅ Check for existing active subscription
        existing = await self._get_active_subscription(payload.user_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User already has an active {existing.plan} subscription"
            )

        # ✅ Calculate start and end dates using utility
        start_date = datetime.now(timezone.utc)
        end_date = calculate_end_date(start_date, payload.plan)

        # ✅ Determine initial status
        initial_status = payload.status if payload.status else SubscriptionStatus.active

        subscription = Subscription(
            user_id=payload.user_id,
            plan=payload.plan,
            status=initial_status,
            start_date=start_date,
            end_date=end_date,  # ✅ Now includes end_date
            payment_id=payload.payment_id,  # ✅ Uses payment_id from payload
        )

        self.db.add(subscription)
        await self.db.commit()
        await self.db.refresh(subscription)

        logger.info(
            f"Created {payload.plan} subscription (ID: {subscription.id}) "
            f"for user {payload.user_id} with status {initial_status}"
        )
        return subscription

    async def get_user_subscription(
            self,
            user_id: int,
            raise_if_not_found: bool = True  # ✅ Added parameter
    ) -> Optional[Subscription]:
        """
        Get the most recent subscription for a user.

        Args:
            user_id: User ID
            raise_if_not_found: Whether to raise exception if not found

        Returns:
            Subscription object or None

        Raises:
            HTTPException: If subscription not found and raise_if_not_found=True
        """
        result = await self.db.execute(
            select(Subscription)
            .options(selectinload(Subscription.user))  # ✅ Eager load user
            .where(Subscription.user_id == user_id)
            .order_by(Subscription.created_at.desc())
        )
        subscription = result.scalar_one_or_none()

        if not subscription and raise_if_not_found:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No subscription found for this user"
            )

        # ✅ Auto-expire if needed
        if subscription:
            await self._auto_expire_if_needed(subscription)

        return subscription

    async def get_subscription_by_id(self, subscription_id: int) -> Subscription:
        """
        Get a subscription by its ID.

        Args:
            subscription_id: Subscription ID

        Returns:
            Subscription object

        Raises:
            HTTPException: If subscription not found
        """
        result = await self.db.execute(
            select(Subscription)
            .options(selectinload(Subscription.user))
            .where(Subscription.id == subscription_id)
        )
        subscription = result.scalar_one_or_none()

        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Subscription with ID {subscription_id} not found"
            )

        await self._auto_expire_if_needed(subscription)
        return subscription

    async def cancel_subscription(
            self,
            subscription_id: int,
            user_id: int,
            reason: Optional[str] = None
    ) -> Subscription:
        """
        Cancel a subscription.

        Args:
            subscription_id: Subscription ID to cancel
            user_id: User ID (for authorization)
            reason: Optional cancellation reason

        Returns:
            Updated subscription object

        Raises:
            HTTPException: If subscription not found, not authorized,
                          or already cancelled/expired
        """
        subscription = await self.get_subscription_by_id(subscription_id)

        # Authorization check
        if subscription.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to cancel this subscription"
            )

        # ✅ Status validation
        if subscription.status == SubscriptionStatus.cancelled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Subscription is already cancelled"
            )

        if subscription.status == SubscriptionStatus.expired:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot cancel an expired subscription"
            )

        subscription.status = SubscriptionStatus.cancelled
        subscription.updated_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(subscription)

        logger.info(
            f"Cancelled subscription {subscription_id} for user {user_id}"
            + (f" - Reason: {reason}" if reason else "")
        )
        return subscription

    async def reactivate_subscription(
            self,
            subscription_id: int,
            user_id: int
    ) -> Subscription:
        """
        Reactivate a cancelled subscription (if not expired).

        Args:
            subscription_id: Subscription ID to reactivate
            user_id: User ID (for authorization)

        Returns:
            Updated subscription object

        Raises:
            HTTPException: If subscription not found, not authorized,
                          not cancelled, or already expired
        """
        subscription = await self.get_subscription_by_id(subscription_id)

        if subscription.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to reactivate this subscription"
            )

        if subscription.status != SubscriptionStatus.cancelled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Can only reactivate cancelled subscriptions. Current status: {subscription.status}"
            )

        if subscription.end_date and subscription.end_date < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot reactivate an expired subscription. Please create a new subscription."
            )

        subscription.status = SubscriptionStatus.active
        subscription.updated_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(subscription)

        logger.info(f"Reactivated subscription {subscription_id} for user {user_id}")
        return subscription

    async def get_subscription_status(self, user_id: int) -> dict:
        """
        Get detailed subscription status for a user.

        Args:
            user_id: User ID

        Returns:
            Dictionary with subscription status details
        """
        subscription = await self.get_user_subscription(user_id, raise_if_not_found=False)

        if not subscription:
            return {
                "has_subscription": False,
                "status": None,
                "plan": None,
                "access_granted": False,
                "end_date": None,
                "message": "No subscription found"
            }

        is_active = subscription.status == SubscriptionStatus.active

        return {
            "has_subscription": True,
            "status": subscription.status,
            "plan": subscription.plan,
            "access_granted": is_active,
            "end_date": subscription.end_date,
            "message": self._get_status_message(subscription)
        }

    async def check_active_subscription(self, user_id: int) -> bool:
        """
        Check if user has an active subscription.

        Args:
            user_id: User ID

        Returns:
            True if user has active subscription, False otherwise
        """
        subscription = await self._get_active_subscription(user_id)

        if not subscription:
            return False

        if subscription.end_date and subscription.end_date < datetime.now(timezone.utc):
            await self._expire_subscription(subscription)
            return False

        return True

