from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.schemas.base import UserBase
from app.schemas.subscription import SubscriptionOut


class UserCreate(BaseModel):
    email: str
    name: Optional[str] = None
    notifications_enabled: bool = True


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

