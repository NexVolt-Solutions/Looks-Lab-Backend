from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional
from app.schemas.user import UserOut
from app.schemas.base import UserBase


class GoogleAuthSchema(BaseModel):
    id_token: str
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    picture: Optional[str] = None


class AppleAuthSchema(BaseModel):
    id_token: str
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    picture: Optional[str] = None


class TokenResponse(BaseModel):
    user: UserOut
    access_token: str
    refresh_token: str


class RefreshTokenBase(BaseModel):
    refresh_token: str
    expires_at: datetime


class RefreshTokenCreate(RefreshTokenBase):
    user_id: int


class RefreshTokenOut(RefreshTokenBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    user: Optional[UserBase] = None

    model_config = {"from_attributes": True}


class SignOutResponse(BaseModel):
    """Response model for sign out endpoint."""
    detail: str

