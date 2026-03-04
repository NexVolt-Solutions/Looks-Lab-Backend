from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.logging import logger
from app.models.subscription import Subscription, SubscriptionStatus
from app.schemas.subscription import SubscriptionCreate
from app.utils.subscription_utils import calculate_end_date


class SubscriptionService:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_subscription(self, payload: SubscriptionCreate) -> Subscription:
        existing = await self._get_active_subscription(payload.user_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User already has an active {existing.plan} subscription"
            )

        start_date = datetime.now(timezone.utc)
        subscription = Subscription(
            user_id=payload.user_id,
            plan=payload.plan,
            status=SubscriptionStatus.active,
            start_date=start_date,
            end_date=calculate_end_date(start_date, payload.plan),
            payment_id=payload.payment_id,
        )
        self.db.add(subscription)
        await self.db.commit()
        await self.db.refresh(subscription)
        logger.info(f"Created {payload.plan} subscription for user {payload.user_id}")
        return subscription

    async def get_user_subscription(self, user_id: int, raise_if_not_found: bool = True) -> Optional[Subscription]:
        result = await self.db.execute(
            select(Subscription)
            .options(selectinload(Subscription.user))
            .where(Subscription.user_id == user_id)
            .order_by(Subscription.created_at.desc())
        )
        subscription = result.scalar_one_or_none()

        if not subscription and raise_if_not_found:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No subscription found for this user")

        if subscription:
            await self._auto_expire_if_needed(subscription)

        return subscription

    async def get_subscription_by_id(self, subscription_id: int) -> Subscription:
        result = await self.db.execute(
            select(Subscription)
            .options(selectinload(Subscription.user))
            .where(Subscription.id == subscription_id)
        )
        subscription = result.scalar_one_or_none()
        if not subscription:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Subscription {subscription_id} not found")
        await self._auto_expire_if_needed(subscription)
        return subscription

    async def cancel_subscription(self, subscription_id: int, user_id: int) -> Subscription:
        subscription = await self.get_subscription_by_id(subscription_id)

        if subscription.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to cancel this subscription")
        if subscription.status == SubscriptionStatus.cancelled:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Subscription is already cancelled")
        if subscription.status == SubscriptionStatus.expired:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot cancel an expired subscription")

        subscription.status = SubscriptionStatus.cancelled
        subscription.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(subscription)
        logger.info(f"Cancelled subscription {subscription_id} for user {user_id}")
        return subscription

    async def reactivate_subscription(self, subscription_id: int, user_id: int) -> Subscription:
        subscription = await self.get_subscription_by_id(subscription_id)

        if subscription.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to reactivate this subscription")
        if subscription.status != SubscriptionStatus.cancelled:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Can only reactivate cancelled subscriptions. Current: {subscription.status}")
        if subscription.end_date and subscription.end_date < datetime.now(timezone.utc):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot reactivate an expired subscription. Please create a new one.")

        subscription.status = SubscriptionStatus.active
        subscription.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(subscription)
        logger.info(f"Reactivated subscription {subscription_id} for user {user_id}")
        return subscription

    async def get_subscription_status(self, user_id: int) -> dict:
        subscription = await self.get_user_subscription(user_id, raise_if_not_found=False)

        if not subscription:
            return {
                "has_subscription": False,
                "status": None,
                "plan": None,
                "access_granted": False,
                "end_date": None,
                "message": "No subscription found",
            }

        return {
            "has_subscription": True,
            "status": subscription.status,
            "plan": subscription.plan,
            "access_granted": subscription.status == SubscriptionStatus.active,
            "end_date": subscription.end_date,
            "message": self._get_status_message(subscription),
        }

    async def check_active_subscription(self, user_id: int) -> bool:
        subscription = await self._get_active_subscription(user_id)
        if not subscription:
            return False
        if subscription.end_date and subscription.end_date < datetime.now(timezone.utc):
            await self._expire_subscription(subscription)
            return False
        return True

    async def _get_active_subscription(self, user_id: int) -> Optional[Subscription]:
        result = await self.db.execute(
            select(Subscription).where(
                Subscription.user_id == user_id,
                Subscription.status == SubscriptionStatus.active,
            )
        )
        return result.scalar_one_or_none()

    async def _auto_expire_if_needed(self, subscription: Subscription) -> None:
        if (
            subscription.status == SubscriptionStatus.active
            and subscription.end_date
            and subscription.end_date < datetime.now(timezone.utc)
        ):
            await self._expire_subscription(subscription)

    async def _expire_subscription(self, subscription: Subscription) -> None:
        subscription.status = SubscriptionStatus.expired
        subscription.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        logger.info(f"Auto-expired subscription {subscription.id} for user {subscription.user_id}")

    def _get_status_message(self, subscription: Subscription) -> str:
        return {
            SubscriptionStatus.active: f"Active {subscription.plan} subscription",
            SubscriptionStatus.cancelled: "Subscription has been cancelled",
            SubscriptionStatus.expired: "Subscription has expired",
        }.get(subscription.status, "Subscription is pending")

