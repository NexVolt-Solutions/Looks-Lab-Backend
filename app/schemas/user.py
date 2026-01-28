"""
User schemas.
Pydantic models for user profile management.
"""
from pydantic import BaseModel
from datetime import datetime

from app.schemas.base import UserBase
from app.schemas.subscription import SubscriptionOut


class UserCreate(BaseModel):
    email: str
    name: str | None = None
    notifications_enabled: bool = True


class UserUpdate(BaseModel):
    name: str | None = None
    age: int | None = None
    gender: str | None = None
    profile_image: str | None = None
    notifications_enabled: bool | None = None


class UserOut(UserBase):
    name: str | None = None
    age: int | None = None
    gender: str | None = None
    profile_image: str | None = None
    notifications_enabled: bool
    created_at: datetime
    updated_at: datetime | None = None
    subscription: SubscriptionOut | None = None

    model_config = {"from_attributes": True}

