import base64
import json
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.core.logging import logger
from app.models.user import User
from app.schemas.iap import (
    IAPReceiptRequest,
    IAPReceiptResponse,
    IAPProductsResponse,
    IAPProduct,
    RestorePurchasesResponse,
)
from app.services.iap_service import IAPService
from app.utils.jwt_utils import get_current_user

router = APIRouter()


@router.post("/validate-receipt", response_model=IAPReceiptResponse)
async def validate_receipt(
    request: IAPReceiptRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    service = IAPService(db)
    result = await service.validate_receipt(user_id=current_user.id, request=request)

    if not result.success:
        raise HTTPException(status_code=400, detail=result.message or "Receipt validation failed")

    return result


@router.post("/restore-purchases", response_model=RestorePurchasesResponse)
async def restore_purchases(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    service = IAPService(db)
    purchases = await service.restore_purchases(current_user.id)

    has_active = len(purchases) > 0
    plan = purchases[0].get("plan") if has_active else None
    expires_at = purchases[0].get("expires_at") if has_active else None

    return RestorePurchasesResponse(
        success=True,
        subscriptions_restored=len(purchases),
        active_subscription=has_active,
        plan=plan,
        expires_at=expires_at,
        message=f"Successfully restored {len(purchases)} subscription(s)" if has_active else "No active subscriptions found"
    )


@router.post("/webhooks/apple")
async def apple_webhook(
    request: Request,
    db: AsyncSession = Depends(get_async_db),
):
    try:
        data = await request.json()
        notification_type = data.get("notification_type")
        logger.info(f"Apple webhook received: {notification_type}")
        # TODO: Handle INITIAL_BUY, DID_RENEW, DID_CHANGE_RENEWAL_STATUS, DID_FAIL_TO_RENEW, REFUND
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Apple webhook error: {e}")
        return {"status": "error", "message": str(e)}


@router.post("/webhooks/google")
async def google_webhook(
    request: Request,
    db: AsyncSession = Depends(get_async_db),
):
    try:
        data = await request.json()
        message = data.get("message", {})

        if "data" in message:
            notification = json.loads(base64.b64decode(message["data"]).decode("utf-8"))
            logger.info(f"Google webhook received: {notification.get('notificationType')}")
            # TODO: Handle SUBSCRIPTION_PURCHASED (1), SUBSCRIPTION_RENEWED (2), SUBSCRIPTION_CANCELED (3), SUBSCRIPTION_RECOVERED (13)

        return {"status": "success"}
    except Exception as e:
        logger.error(f"Google webhook error: {e}")
        return {"status": "error", "message": str(e)}


@router.get("/products", response_model=IAPProductsResponse)
async def get_iap_products():
    return IAPProductsResponse(
        products=[
            IAPProduct(id="com.lookslab.weekly", type="subscription", platform="ios", name="Weekly Subscription", description="Looks Lab Premium - Weekly"),
            IAPProduct(id="com.lookslab.monthly", type="subscription", platform="ios", name="Monthly Subscription", description="Looks Lab Premium - Monthly"),
            IAPProduct(id="com.lookslab.yearly", type="subscription", platform="ios", name="Yearly Subscription", description="Looks Lab Premium - Yearly (Save 17%)"),
            IAPProduct(id="looks_lab_weekly", type="subscription", platform="android", name="Weekly Subscription", description="Looks Lab Premium - Weekly"),
            IAPProduct(id="looks_lab_monthly", type="subscription", platform="android", name="Monthly Subscription", description="Looks Lab Premium - Monthly"),
            IAPProduct(id="looks_lab_yearly", type="subscription", platform="android", name="Yearly Subscription", description="Looks Lab Premium - Yearly (Save 17%)"),
        ]
    )

