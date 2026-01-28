"""
Subscription schemas.
Pydantic models for subscription management.
"""
from pydantic import BaseModel
from datetime import datetime
from enum import Enum

from app.schemas.base import UserBase


class PlanType(str, Enum):
    weekly = "weekly"
    monthly = "monthly"
    yearly = "yearly"


class SubscriptionStatus(str, Enum):
    pending = "pending"
    active = "active"
    expired = "expired"
    cancelled = "cancelled"


class SubscriptionBase(BaseModel):
    plan: PlanType
    status: SubscriptionStatus | None = None


class SubscriptionCreate(SubscriptionBase):
    user_id: int


class SubscriptionOut(BaseModel):
    id: int
    user_id: int
    plan: PlanType
    status: SubscriptionStatus
    start_date: datetime
    end_date: datetime | None = None
    created_at: datetime
    updated_at: datetime | None = None
    payment_id: str | None = None
    user: UserBase | None = None

    model_config = {"from_attributes": True}

