from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum


class IAPProvider(str, Enum):
    apple = "apple"
    google = "google"


class IAPReceiptRequest(BaseModel):
    provider: IAPProvider
    product_id: str
    receipt_data: str
    purchase_token: Optional[str] = None


class IAPReceiptResponse(BaseModel):
    success: bool
    subscription_active: bool
    plan: Optional[str] = None
    expires_at: Optional[datetime] = None
    message: Optional[str] = None


class IAPProduct(BaseModel):
    id: str
    type: str
    platform: str
    name: str
    description: str


class IAPProductsResponse(BaseModel):
    products: List[IAPProduct]


class RestorePurchasesResponse(BaseModel):
    success: bool
    subscriptions_restored: int
    active_subscription: bool
    plan: Optional[str] = None
    expires_at: Optional[datetime] = None
    message: str


class AppleReceiptData(BaseModel):
    receipt_data: str = Field(..., alias="receipt-data")
    password: str
    exclude_old_transactions: bool = Field(True, alias="exclude-old-transactions")


class AppleReceiptResponse(BaseModel):
    status: int
    latest_receipt_info: Optional[List[dict]] = None
    pending_renewal_info: Optional[List[dict]] = None
    environment: Optional[str] = None

