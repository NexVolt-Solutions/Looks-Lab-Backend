"""
In-App Purchase service.
Handles receipt validation for Apple App Store and Google Play Store.
"""
from datetime import datetime, timezone
import httpx
import base64
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.core.logging import logger
from app.models.subscription import Subscription
from app.models.user import User
from app.schemas.subscription import SubscriptionStatus
from app.schemas.iap import (
    IAPProvider,
    IAPReceiptRequest,
    IAPReceiptResponse,
    AppleReceiptData,
    AppleReceiptResponse,
)


class IAPService:
    """In-App Purchase validation service."""
    
    # Apple endpoints
    APPLE_PRODUCTION_URL = "https://buy.itunes.apple.com/verifyReceipt"
    APPLE_SANDBOX_URL = "https://sandbox.itunes.apple.com/verifyReceipt"
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def validate_receipt(
        self,
        user_id: int,
        request: IAPReceiptRequest
    ) -> IAPReceiptResponse:
        """
        Validate in-app purchase receipt.
        
        Args:
            user_id: User ID from authenticated session
            request: Receipt validation request
            
        Returns:
            IAPReceiptResponse with validation result
        """
        try:
            if request.provider == IAPProvider.APPLE:
                return await self._validate_apple_receipt(user_id, request)
            elif request.provider == IAPProvider.GOOGLE:
                return await self._validate_google_receipt(user_id, request)
            else:
                return IAPReceiptResponse(
                    success=False,
                    subscription_active=False,
                    message="Invalid provider"
                )
        except Exception as e:
            logger.error(f"Receipt validation error: {e}")
            return IAPReceiptResponse(
                success=False,
                subscription_active=False,
                message=str(e)
            )
    
    async def _validate_apple_receipt(
        self,
        user_id: int,
        request: IAPReceiptRequest
    ) -> IAPReceiptResponse:
        """
        Validate Apple App Store receipt.
        
        Returns:
            IAPReceiptResponse with validation result
        """
        # Prepare request to Apple
        payload = AppleReceiptData(
            receipt_data=request.receipt_data,
            password=settings.APPLE_SHARED_SECRET,
            exclude_old_transactions=True
        )
        
        # Try production first
        is_valid, receipt_info = await self._call_apple_api(
            self.APPLE_PRODUCTION_URL,
            payload
        )
        
        # If production fails with 21007 (sandbox receipt), try sandbox
        if not is_valid and receipt_info and receipt_info.get("status") == 21007:
            logger.info("Retrying with Apple sandbox")
            is_valid, receipt_info = await self._call_apple_api(
                self.APPLE_SANDBOX_URL,
                payload
            )
        
        if not is_valid or not receipt_info:
            return IAPReceiptResponse(
                success=False,
                subscription_active=False,
                message=f"Apple validation failed: {receipt_info.get('status') if receipt_info else 'Unknown error'}"
            )
        
        # Extract latest receipt info
        latest_info = receipt_info.get("latest_receipt_info", [])
        if not latest_info:
            return IAPReceiptResponse(
                success=False,
                subscription_active=False,
                message="No receipt info found"
            )
        
        # Get the most recent transaction
        latest_transaction = latest_info[0]
        
        # Extract expiration date
        expires_ms = latest_transaction.get("expires_date_ms")
        if not expires_ms:
            return IAPReceiptResponse(
                success=False,
                subscription_active=False,
                message="No expiration date found"
            )
        
        expiration_date = datetime.fromtimestamp(
            int(expires_ms) / 1000,
            tz=timezone.utc
        )
        
        # Check if subscription is currently active
        is_active = expiration_date > datetime.now(timezone.utc)
        
        # Update subscription in database
        plan = self._get_plan_from_product_id(request.product_id)
        await self._update_subscription(
            user_id=user_id,
            product_id=request.product_id,
            plan=plan,
            status=SubscriptionStatus.ACTIVE if is_active else SubscriptionStatus.EXPIRED,
            expiration_date=expiration_date
        )
        
        logger.info(f"? Apple receipt validated for user {user_id}")
        
        return IAPReceiptResponse(
            success=True,
            subscription_active=is_active,
            plan=plan,
            expires_at=expiration_date,
            message="Receipt validated successfully"
        )
    
    async def _call_apple_api(
        self,
        url: str,
        payload: AppleReceiptData
    ) -> tuple[bool, dict | None]:
        """
        Call Apple receipt validation API.
        
        Returns:
            (is_valid, receipt_data)
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    json=payload.model_dump(by_alias=True),
                    timeout=30.0
                )
                data = response.json()
                
                # Status code 0 means success
                is_valid = data.get("status") == 0
                return is_valid, data
                
        except Exception as e:
            logger.error(f"Apple API call failed: {e}")
            return False, None
    
    async def _validate_google_receipt(
        self,
        user_id: int,
        request: IAPReceiptRequest
    ) -> IAPReceiptResponse:
        """
        Validate Google Play Store receipt.
        
        Note: Requires Google Play Developer API setup.
        For now, this is a placeholder that returns success for testing.
        """
        # TODO: Implement Google Play Developer API integration
        # This requires:
        # 1. Service account JSON key
        # 2. Google API Python client library
        # 3. Proper authentication and API calls
        
        logger.warning("?? Google Play validation not fully implemented yet")
        
        # For testing: Accept all Google receipts
        # In production, this should validate with Google API
        plan = self._get_plan_from_product_id(request.product_id)
        expiration_date = datetime.now(timezone.utc).replace(
            month=datetime.now(timezone.utc).month + 1
        )  # Mock: 1 month from now
        
        await self._update_subscription(
            user_id=user_id,
            product_id=request.product_id,
            plan=plan,
            status=SubscriptionStatus.ACTIVE,
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
        """Update or create subscription in database."""
        # Check if subscription exists
        result = await self.db.execute(
            select(Subscription).where(Subscription.user_id == user_id)
        )
        subscription = result.scalar_one_or_none()
        
        if subscription:
            # Update existing subscription
            subscription.plan = plan
            subscription.status = status
            subscription.current_period_end = expiration_date
            subscription.payment_id = product_id
            subscription.updated_at = datetime.now(timezone.utc)
            logger.info(f"Updated subscription for user {user_id}")
        else:
            # Create new subscription
            subscription = Subscription(
                user_id=user_id,
                plan=plan,
                status=status,
                current_period_start=datetime.now(timezone.utc),
                current_period_end=expiration_date,
                payment_id=product_id,
                cancel_at_period_end=False
            )
            self.db.add(subscription)
            logger.info(f"Created subscription for user {user_id}")
        
        await self.db.commit()
        await self.db.refresh(subscription)
    
    def _get_plan_from_product_id(self, product_id: str) -> str:
        """Map product ID to subscription plan."""
        product_lower = product_id.lower()
        
        if "weekly" in product_lower or "week" in product_lower:
            return "weekly"
        elif "monthly" in product_lower or "month" in product_lower:
            return "monthly"
        elif "yearly" in product_lower or "annual" in product_lower:
            return "yearly"
        else:
            # Default to monthly
            logger.warning(f"Unknown product ID: {product_id}, defaulting to monthly")
            return "monthly"
    
    async def restore_purchases(self, user_id: int) -> list[IAPReceiptResponse]:
        """
        Restore previous purchases for a user.
        This would query the user's purchase history from Apple/Google.
        
        For now, returns current subscription if exists.
        """
        result = await self.db.execute(
            select(Subscription).where(Subscription.user_id == user_id)
        )
        subscription = result.scalar_one_or_none()
        
        if subscription and subscription.status == SubscriptionStatus.ACTIVE:
            return [IAPReceiptResponse(
                success=True,
                subscription_active=True,
                plan=subscription.plan,
                expires_at=subscription.current_period_end,
                message="Active subscription found"
            )]
        
        return []
        
        