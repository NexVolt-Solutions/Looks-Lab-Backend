from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from app.schemas.base import UserBase
from app.schemas.subscription import SubscriptionOut


class UserUpdate(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    profile_image: Optional[str] = None
    notifications_enabled: Optional[bool] = None


class UserOut(UserBase):
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    profile_image: Optional[str] = None
    notifications_enabled: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    subscription: Optional[SubscriptionOut] = None

    model_config = {"from_attributes": True}


class DailyScore(BaseModel):
    day: str
    date: str
    score: float = Field(..., ge=0, le=100)


class WeeklyProgressOut(BaseModel):
    user_id: int
    labels: list[str]
    scores: list[float]
    days: list[DailyScore]
    week_average: float = Field(..., ge=0, le=100)

