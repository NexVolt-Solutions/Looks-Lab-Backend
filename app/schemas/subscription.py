from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field

from app.models.enums import PlanType, SubscriptionStatus
from app.schemas.base import UserBase


class SubscriptionInterval(str, Enum):
    week = "week"
    month = "month"
    year = "year"


class SubscriptionPlanOut(BaseModel):
    id: str
    type: PlanType
    name: str
    price: float = Field(..., gt=0)
    currency: str = "USD"
    interval: SubscriptionInterval
    interval_count: int = 1
    features: List[str]
    description: str
    duration_days: int = Field(..., gt=0)
    is_popular: bool = False
    savings_percent: Optional[int] = None


class SubscriptionCreate(BaseModel):
    plan: PlanType
    user_id: int
    payment_id: Optional[str] = None


class SubscriptionUpdate(BaseModel):
    plan: Optional[PlanType] = None
    status: Optional[SubscriptionStatus] = None
    end_date: Optional[datetime] = None
    payment_id: Optional[str] = None


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


class SubscriptionStatusResponse(BaseModel):
    has_subscription: bool
    status: Optional[SubscriptionStatus] = None
    plan: Optional[PlanType] = None
    access_granted: bool
    end_date: Optional[datetime] = None
    message: str

