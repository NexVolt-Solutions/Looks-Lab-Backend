"""
In-App Purchase routes.
Receipt validation and webhook handling for Apple and Google.
"""
from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.ext.asyncio import AsyncSession
import hmac
import hashlib

from app.core.database import get_async_db
from app.utils.jwt_utils import get_current_user
from app.core.logging import logger
from app.models.user import User
from app.schemas.iap import (
    IAPReceiptRequest,
    IAPReceiptResponse,
)
from app.services.iap_service import IAPService


router = APIRouter()


@router.post("/validate-receipt", response_model=IAPReceiptResponse)
async def validate_receipt(
    request: IAPReceiptRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Validate in-app purchase receipt from mobile app.
    
    This endpoint is called after a user makes a purchase in the mobile app.
    It validates the receipt with Apple or Google and updates the subscription.
    
    **Flow:**
    1. User completes purchase in mobile app
    2. App receives receipt from Apple/Google
    3. App calls this endpoint with receipt data
    4. Backend validates receipt with store
    5. Backend updates subscription in database
    6. App unlocks premium features
    
    **Supports:**
    - Apple App Store (iOS)
    - Google Play Store (Android)
    """
    logger.info(
        f"?? Receipt validation request from user {current_user.id} "
        f"({request.provider.value})"
    )
    
    service = IAPService(db)
    result = await service.validate_receipt(
        user_id=current_user.id,
        request=request
    )
    
    if not result.success:
        logger.warning(f"? Receipt validation failed: {result.message}")
        raise HTTPException(
            status_code=400,
            detail=result.message or "Receipt validation failed"
        )
    
    logger.info(
        f"? Receipt validated successfully for user {current_user.id}. "
        f"Plan: {result.plan}, Active: {result.subscription_active}"
    )
    
    return result


@router.post("/restore-purchases")
async def restore_purchases(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Restore previous purchases for a user.
    
    This is called when a user reinstalls the app or signs in on a new device.
    It checks if the user has any active subscriptions and restores them.
    
    **Use cases:**
    - User reinstalls app
    - User signs in on new device
    - User switches from iOS to Android (same account)
    """
    logger.info(f"?? Restore purchases request from user {current_user.id}")
    
    service = IAPService(db)
    purchases = await service.restore_purchases(current_user.id)
    
    return {
        "success": True,
        "purchases": purchases,
        "message": f"Found {len(purchases)} active subscription(s)"
    }


@router.post("/webhooks/apple")
async def apple_webhook(
    request: Request,
    db: AsyncSession = Depends(get_async_db),
):
    """
    Handle Apple App Store Server Notifications.
    
    Apple sends webhooks for:
    - Initial purchase
    - Subscription renewal
    - Subscription cancellation
    - Refund
    - Billing issue
    
    **Setup:**
    1. Go to App Store Connect
    2. Navigate to your app ? App Information
    3. Set Production Server URL to: https://your-api.com/api/v1/iap/webhooks/apple
    4. Save
    
    **Note:** This endpoint is called by Apple, not your mobile app.
    """
    # Get raw body
    body = await request.body()
    
    # TODO: Verify webhook signature from Apple
    # Apple includes a signature in headers that should be verified
    
    try:
        # Parse webhook data
        data = await request.json()
        
        logger.info(f"?? Apple webhook received: {data.get('notification_type')}")
        
        # Extract notification type and data
        notification_type = data.get("notification_type")
        unified_receipt = data.get("unified_receipt", {})
        
        # TODO: Process different notification types
        # - INITIAL_BUY
        # - DID_RENEW
        # - DID_CHANGE_RENEWAL_STATUS
        # - DID_FAIL_TO_RENEW
        # - REFUND
        
        logger.info("? Apple webhook processed")
        
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"? Apple webhook error: {e}")
        return {"status": "error", "message": str(e)}


@router.post("/webhooks/google")
async def google_webhook(
    request: Request,
    db: AsyncSession = Depends(get_async_db),
):
    """
    Handle Google Play Real-Time Developer Notifications.
    
    Google sends webhooks for:
    - Subscription purchased
    - Subscription renewed
    - Subscription canceled
    - Subscription paused/recovered
    - Grace period
    
    **Setup:**
    1. Go to Google Play Console
    2. Navigate to your app ? Monetization setup
    3. Set Real-time developer notifications to: https://your-api.com/api/v1/iap/webhooks/google
    4. Save
    
    **Note:** This endpoint is called by Google, not your mobile app.
    """
    try:
        # Parse Pub/Sub message
        data = await request.json()
        message = data.get("message", {})
        
        # Decode base64 data
        import base64
        if "data" in message:
            decoded = base64.b64decode(message["data"]).decode("utf-8")
            notification = eval(decoded)  # TODO: Use json.loads instead
            
            logger.info(f"?? Google webhook received: {notification.get('notificationType')}")
            
            # TODO: Process different notification types
            # - SUBSCRIPTION_PURCHASED (1)
            # - SUBSCRIPTION_CANCELED (3)
            # - SUBSCRIPTION_RENEWED (2)
            # - SUBSCRIPTION_RECOVERED (13)
            
            logger.info("? Google webhook processed")
        
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"? Google webhook error: {e}")
        return {"status": "error", "message": str(e)}


@router.get("/products")
async def get_iap_products():
    """
    Get available in-app purchase products.
    
    Returns product IDs that the mobile app should query from the store.
    This is useful for displaying available subscription plans.
    """
    return {
        "products": [
            {
                "id": "com.lookslab.weekly",
                "type": "subscription",
                "platform": "ios",
                "name": "Weekly Subscription",
                "description": "Looks Lab Premium - Weekly",
            },
            {
                "id": "com.lookslab.monthly",
                "type": "subscription",
                "platform": "ios",
                "name": "Monthly Subscription",
                "description": "Looks Lab Premium - Monthly",
            },
            {
                "id": "com.lookslab.yearly",
                "type": "subscription",
                "platform": "ios",
                "name": "Yearly Subscription",
                "description": "Looks Lab Premium - Yearly (Save 17%)",
            },
            {
                "id": "looks_lab_weekly",
                "type": "subscription",
                "platform": "android",
                "name": "Weekly Subscription",
                "description": "Looks Lab Premium - Weekly",
            },
            {
                "id": "looks_lab_monthly",
                "type": "subscription",
                "platform": "android",
                "name": "Monthly Subscription",
                "description": "Looks Lab Premium - Monthly",
            },
            {
                "id": "looks_lab_yearly",
                "type": "subscription",
                "platform": "android",
                "name": "Yearly Subscription",
                "description": "Looks Lab Premium - Yearly (Save 17%)",
            },
        ]
    }
    
    