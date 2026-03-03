from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import List, Optional
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


class SubscriptionInterval(str, Enum):
    week = "week"
    month = "month"
    year = "year"


class SubscriptionPlanOut(BaseModel):
    id: str
    type: PlanType
    name: str
    price: float = Field(..., gt=0)
    currency: str = Field(default="USD")
    interval: SubscriptionInterval
    interval_count: int = Field(default=1, ge=1)
    features: List[str] = Field(..., min_length=1)
    description: str
    duration_days: int = Field(..., gt=0)
    is_popular: bool = Field(default=False)
    savings_percent: Optional[int] = Field(default=None, ge=0, le=100)


class SubscriptionCreate(BaseModel):
    plan: PlanType
    user_id: int
    payment_id: Optional[str] = None

    @field_validator('plan')
    @classmethod
    def validate_plan(cls, v):
        if v not in PlanType.__members__.values():
            raise ValueError(f"Invalid plan. Must be: {', '.join(PlanType.__members__.keys())}")
        return v


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

