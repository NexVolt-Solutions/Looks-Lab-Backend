"""
In-App Purchase schemas for receipt validation.
Supports both Apple App Store and Google Play Store.
"""
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class IAPProvider(str, Enum):
    """In-App Purchase provider."""
    APPLE = "apple"
    GOOGLE = "google"


class IAPReceiptRequest(BaseModel):
    """Receipt validation request from mobile app."""
    provider: IAPProvider = Field(..., description="Payment provider (apple or google)")
    product_id: str = Field(..., description="Product SKU/ID purchased")
    receipt_data: str = Field(..., description="Receipt data from store")
    purchase_token: str | None = Field(None, description="Google Play purchase token (Android only)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "provider": "apple",
                "product_id": "com.lookslab.monthly",
                "receipt_data": "MIIT8gYJKoZIhvcNAQcCoIIT4...",
                "purchase_token": None
            }
        }


class IAPReceiptResponse(BaseModel):
    """Receipt validation response."""
    success: bool = Field(..., description="Whether validation succeeded")
    subscription_active: bool = Field(..., description="Whether subscription is active")
    plan: str | None = Field(None, description="Subscription plan (weekly/monthly/yearly)")
    expires_at: datetime | None = Field(None, description="Subscription expiration date")
    message: str | None = Field(None, description="Error message if validation failed")


class IAPProduct(BaseModel):
    """Single IAP product/subscription plan."""
    id: str = Field(..., description="Product ID (e.g., com.lookslab.weekly)")
    type: str = Field(..., description="Product type (e.g., subscription)")
    platform: str = Field(..., description="Platform (ios or android)")
    name: str = Field(..., description="Display name")
    description: str = Field(..., description="Product description")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "com.lookslab.weekly",
                "type": "subscription",
                "platform": "ios",
                "name": "Weekly Subscription",
                "description": "Looks Lab Premium - Weekly"
            }
        }


class IAPProductsResponse(BaseModel):
    """Response for GET /products endpoint."""
    products: list[IAPProduct] = Field(..., description="Available subscription products")
    
    class Config:
        json_schema_extra = {
            "example": {
                "products": [
                    {
                        "id": "com.lookslab.weekly",
                        "type": "subscription",
                        "platform": "ios",
                        "name": "Weekly Subscription",
                        "description": "Looks Lab Premium - Weekly"
                    },
                    {
                        "id": "com.lookslab.monthly",
                        "type": "subscription",
                        "platform": "ios",
                        "name": "Monthly Subscription",
                        "description": "Looks Lab Premium - Monthly"
                    }
                ]
            }
        }


class RestorePurchasesResponse(BaseModel):
    """Response for POST /restore-purchases endpoint."""
    success: bool = Field(..., description="Whether restore was successful")
    subscriptions_restored: int = Field(..., description="Number of subscriptions restored")
    active_subscription: bool = Field(..., description="Whether user has active subscription")
    plan: str | None = Field(None, description="Active plan (weekly/monthly/yearly)")
    expires_at: datetime | None = Field(None, description="Subscription expiration date")
    message: str = Field(..., description="Status message")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "subscriptions_restored": 1,
                "active_subscription": True,
                "plan": "monthly",
                "expires_at": "2026-03-25T12:00:00Z",
                "message": "Successfully restored 1 subscription"
            }
        }


class AppleReceiptData(BaseModel):
    """Apple App Store receipt validation request to Apple."""
    receipt_data: str = Field(..., alias="receipt-data")
    password: str  # Shared secret from App Store Connect
    exclude_old_transactions: bool = Field(True, alias="exclude-old-transactions")


class AppleReceiptResponse(BaseModel):
    """Apple receipt validation response."""
    status: int
    latest_receipt_info: list[dict] | None = None
    pending_renewal_info: list[dict] | None = None
    environment: str | None = None


class GoogleReceiptRequest(BaseModel):
    """Google Play receipt validation request."""
    product_id: str
    purchase_token: str


class GoogleReceiptResponse(BaseModel):
    """Google Play receipt validation response."""
    kind: str | None = None
    purchaseTimeMillis: str | None = None
    purchaseState: int | None = None
    consumptionState: int | None = None
    autoRenewing: bool | None = None
    expiryTimeMillis: str | None = None


class WebhookEventType(str, Enum):
    """Webhook event types from stores."""
    # Apple
    INITIAL_BUY = "INITIAL_BUY"
    DID_RENEW = "DID_RENEW"
    DID_CHANGE_RENEWAL_STATUS = "DID_CHANGE_RENEWAL_STATUS"
    DID_FAIL_TO_RENEW = "DID_FAIL_TO_RENEW"
    DID_RECOVER = "DID_RECOVER"
    REFUND = "REFUND"
    
    # Google
    SUBSCRIPTION_PURCHASED = "SUBSCRIPTION_PURCHASED"
    SUBSCRIPTION_RENEWED = "SUBSCRIPTION_RENEWED"
    SUBSCRIPTION_CANCELED = "SUBSCRIPTION_CANCELED"
    SUBSCRIPTION_EXPIRED = "SUBSCRIPTION_EXPIRED"
    SUBSCRIPTION_PAUSED = "SUBSCRIPTION_PAUSED"
    SUBSCRIPTION_RECOVERED = "SUBSCRIPTION_RECOVERED"


class StoreWebhook(BaseModel):
    """Generic webhook from App Store or Play Store."""
    provider: IAPProvider
    event_type: WebhookEventType
    user_id: int
    product_id: str
    transaction_id: str | None = None
    expiration_date: datetime | None = None
    cancellation_date: datetime | None = None
    raw_data: dict  # Original webhook payload
    
    