"""
Subscription schemas.
Pydantic models for subscription management.
"""
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import List, Optional
from enum import Enum

from app.schemas.base import UserBase


class PlanType(str, Enum):
    """Subscription plan types."""
    weekly = "weekly"
    monthly = "monthly"
    yearly = "yearly"


class SubscriptionStatus(str, Enum):
    """Subscription status types."""
    pending = "pending"
    active = "active"
    expired = "expired"
    cancelled = "cancelled"


class SubscriptionInterval(str, Enum):
    """Billing interval types."""
    week = "week"
    month = "month"
    year = "year"


# ==================== SUBSCRIPTION PLAN SCHEMAS ====================

class SubscriptionPlanOut(BaseModel):
    """
    Output schema for subscription plans.
    Used for GET /subscriptions/plans endpoint.
    """
    id: str = Field(..., description="Unique plan identifier")
    type: PlanType = Field(..., description="Plan type")
    name: str = Field(..., description="Display name")
    price: float = Field(..., gt=0, description="Price in USD")
    currency: str = Field(default="USD", description="Currency code")
    interval: SubscriptionInterval = Field(..., description="Billing interval")
    interval_count: int = Field(default=1, ge=1, description="Interval count")
    features: List[str] = Field(..., min_length=1, description="Features")
    description: str = Field(..., description="Description")
    duration_days: int = Field(..., gt=0, description="Duration in days")
    is_popular: bool = Field(default=False, description="Popular badge")
    savings_percent: Optional[int] = Field(default=None, ge=0, le=100, description="Savings %")


# ==================== SUBSCRIPTION SCHEMAS ====================

class SubscriptionBase(BaseModel):
    """Base subscription schema."""
    plan: PlanType
    status: Optional[SubscriptionStatus] = None


class SubscriptionCreate(SubscriptionBase):
    """Schema for creating subscription."""
    user_id: int
    payment_id: Optional[str] = Field(default=None, description="Payment gateway ID")

    @field_validator('plan')
    @classmethod
    def validate_plan(cls, v):
        """Ensure valid plan type."""
        if v not in PlanType.__members__.values():
            raise ValueError(f"Invalid plan. Must be: {', '.join(PlanType.__members__.keys())}")
        return v


class SubscriptionUpdate(BaseModel):
    """Schema for updating subscription."""
    plan: Optional[PlanType] = None
    status: Optional[SubscriptionStatus] = None
    end_date: Optional[datetime] = None
    payment_id: Optional[str] = None


class SubscriptionOut(BaseModel):
    """Output schema for subscription."""
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
    """Response for subscription status check."""
    has_subscription: bool
    status: Optional[SubscriptionStatus] = None
    plan: Optional[PlanType] = None
    access_granted: bool
    end_date: Optional[datetime] = None
    message: str

