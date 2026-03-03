from datetime import datetime, timezone
from typing import Optional
import httpx
import base64
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.core.logging import logger
from app.models.subscription import Subscription
from app.schemas.subscription import SubscriptionStatus
from app.schemas.iap import (
    IAPProvider,
    IAPReceiptRequest,
    IAPReceiptResponse,
    AppleReceiptData,
)


class IAPService:
    APPLE_PRODUCTION_URL = "https://buy.itunes.apple.com/verifyReceipt"
    APPLE_SANDBOX_URL = "https://sandbox.itunes.apple.com/verifyReceipt"

    def __init__(self, db: AsyncSession):
        self.db = db

    async def validate_receipt(self, user_id: int, request: IAPReceiptRequest) -> IAPReceiptResponse:
        try:
            if request.provider == IAPProvider.apple:
                return await self._validate_apple_receipt(user_id, request)
            elif request.provider == IAPProvider.google:
                return await self._validate_google_receipt(user_id, request)
            return IAPReceiptResponse(success=False, subscription_active=False, message="Invalid provider")
        except Exception as e:
            logger.error(f"Receipt validation error: {e}")
            return IAPReceiptResponse(success=False, subscription_active=False, message=str(e))

    async def _validate_apple_receipt(self, user_id: int, request: IAPReceiptRequest) -> IAPReceiptResponse:
        payload = AppleReceiptData(
            **{"receipt-data": request.receipt_data, "password": settings.APPLE_SHARED_SECRET, "exclude-old-transactions": True}
        )

        is_valid, receipt_info = await self._call_apple_api(self.APPLE_PRODUCTION_URL, payload)

        if not is_valid and receipt_info and receipt_info.get("status") == 21007:
            logger.info("Retrying with Apple sandbox")
            is_valid, receipt_info = await self._call_apple_api(self.APPLE_SANDBOX_URL, payload)

        if not is_valid or not receipt_info:
            return IAPReceiptResponse(
                success=False,
                subscription_active=False,
                message=f"Apple validation failed: {receipt_info.get('status') if receipt_info else 'Unknown error'}"
            )

        latest_info = receipt_info.get("latest_receipt_info", [])
        if not latest_info:
            return IAPReceiptResponse(success=False, subscription_active=False, message="No receipt info found")

        latest_transaction = latest_info[0]
        expires_ms = latest_transaction.get("expires_date_ms")
        if not expires_ms:
            return IAPReceiptResponse(success=False, subscription_active=False, message="No expiration date found")

        expiration_date = datetime.fromtimestamp(int(expires_ms) / 1000, tz=timezone.utc)
        is_active = expiration_date > datetime.now(timezone.utc)
        plan = self._get_plan_from_product_id(request.product_id)

        await self._update_subscription(
            user_id=user_id,
            product_id=request.product_id,
            plan=plan,
            status=SubscriptionStatus.active if is_active else SubscriptionStatus.expired,
            expiration_date=expiration_date
        )

        logger.info(f"Apple receipt validated for user {user_id}")
        return IAPReceiptResponse(
            success=True,
            subscription_active=is_active,
            plan=plan,
            expires_at=expiration_date,
            message="Receipt validated successfully"
        )

    async def _call_apple_api(self, url: str, payload: AppleReceiptData) -> tuple:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload.model_dump(by_alias=True), timeout=30.0)
                data = response.json()
                return data.get("status") == 0, data
        except Exception as e:
            logger.error(f"Apple API call failed: {e}")
            return False, None

    async def _validate_google_receipt(self, user_id: int, request: IAPReceiptRequest) -> IAPReceiptResponse:
        # TODO: Implement Google Play Developer API integration
        logger.warning("Google Play validation not implemented yet")

        plan = self._get_plan_from_product_id(request.product_id)
        now = datetime.now(timezone.utc)
        expiration_date = now.replace(month=now.month + 1 if now.month < 12 else 1,
                                      year=now.year if now.month < 12 else now.year + 1)

        await self._update_subscription(
            user_id=user_id,
            product_id=request.product_id,
            plan=plan,
            status=SubscriptionStatus.active,
            expiration_date=expiration_date
        )

        return IAPReceiptResponse(
            success=True,
            subscription_active=True,
            plan=plan,
            expires_at=expiration_date,
            message="Receipt validated (Google validation pending implementation)"
        )

    async def _update_subscription(
        self,
        user_id: int,
        product_id: str,
        plan: str,
        status: SubscriptionStatus,
        expiration_date: datetime
    ):
        result = await self.db.execute(select(Subscription).where(Subscription.user_id == user_id))
        subscription = result.scalar_one_or_none()

        if subscription:
            subscription.plan = plan
            subscription.status = status
            subscription.end_date = expiration_date
            subscription.payment_id = product_id
            subscription.updated_at = datetime.now(timezone.utc)
            logger.info(f"Updated subscription for user {user_id}")
        else:
            subscription = Subscription(
                user_id=user_id,
                plan=plan,
                status=status,
                start_date=datetime.now(timezone.utc),
                end_date=expiration_date,
                payment_id=product_id,
            )
            self.db.add(subscription)
            logger.info(f"Created subscription for user {user_id}")

        await self.db.commit()
        await self.db.refresh(subscription)

    def _get_plan_from_product_id(self, product_id: str) -> str:
        product_lower = product_id.lower()
        if "weekly" in product_lower or "week" in product_lower:
            return "weekly"
        elif "yearly" in product_lower or "annual" in product_lower:
            return "yearly"
        else:
            if "monthly" not in product_lower:
                logger.warning(f"Unknown product ID: {product_id}, defaulting to monthly")
            return "monthly"

    async def restore_purchases(self, user_id: int) -> list:
        result = await self.db.execute(select(Subscription).where(Subscription.user_id == user_id))
        subscription = result.scalar_one_or_none()

        if subscription and subscription.status == SubscriptionStatus.active:
            return [{"plan": subscription.plan, "expires_at": subscription.end_date}]

        return []

