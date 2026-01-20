from pydantic import BaseModel
from datetime import datetime
from typing import Optional
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
    status: Optional[SubscriptionStatus] = None


class SubscriptionCreate(SubscriptionBase):
    user_id: int


class SubscriptionOut(BaseModel):
    id: int
    user_id: int
    plan: PlanType
    status: SubscriptionStatus
    start_date: datetime
    end_date: Optional[datetime] = None

    created_at: datetime
    updated_at: Optional[datetime] = None

    payment_id: Optional[str] = None
    user: Optional[UserBase] = None

    model_config = {"from_attributes": True}

