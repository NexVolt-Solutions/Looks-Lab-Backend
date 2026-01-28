"""
Subscription service layer.
Handles subscription operations (create, cancel, check status).
"""
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from app.models.subscription import Subscription, SubscriptionStatus
from app.schemas.subscription import SubscriptionCreate
from app.core.logging import logger


class SubscriptionService:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_subscription(self, payload: SubscriptionCreate) -> Subscription:
        subscription = Subscription(
            user_id=payload.user_id,
            plan=payload.plan,
            status=SubscriptionStatus.active,
            start_date=datetime.now(timezone.utc),
            payment_id=None,
        )

        self.db.add(subscription)
        await self.db.commit()
        await self.db.refresh(subscription)

        logger.info(f"Created {payload.plan} subscription for user {payload.user_id}")
        return subscription

    async def get_user_subscription(self, user_id: int) -> Subscription:
        result = await self.db.execute(
            select(Subscription)
            .where(Subscription.user_id == user_id)
            .order_by(Subscription.created_at.desc())
        )
        subscription = result.scalar_one_or_none()

        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No subscription found"
            )

        return subscription

    async def cancel_subscription(self, subscription_id: int, user_id: int) -> Subscription:
        result = await self.db.execute(
            select(Subscription).where(Subscription.id == subscription_id)
        )
        subscription = result.scalar_one_or_none()

        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription not found"
            )

        if subscription.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized"
            )

        subscription.status = SubscriptionStatus.cancelled
        subscription.updated_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(subscription)

        logger.info(f"Cancelled subscription {subscription_id} for user {user_id}")
        return subscription

    async def check_active_subscription(self, user_id: int) -> bool:
        result = await self.db.execute(
            select(Subscription).where(
                Subscription.user_id == user_id,
                Subscription.status == SubscriptionStatus.active
            )
        )
        subscription = result.scalar_one_or_none()

        if not subscription:
            return False

        if subscription.end_date and subscription.end_date < datetime.now(timezone.utc):
            subscription.status = SubscriptionStatus.expired
            await self.db.commit()
            return False

        return True

