"""
Authentication schemas.
Pydantic models for auth requests and responses.
"""
from pydantic import BaseModel, EmailStr
from datetime import datetime

from app.schemas.user import UserOut
from app.schemas.base import UserBase


class GoogleAuthSchema(BaseModel):
    id_token: str
    email: EmailStr | None = None
    name: str | None = None
    picture: str | None = None


class AppleAuthSchema(BaseModel):
    id_token: str
    email: EmailStr | None = None
    name: str | None = None
    picture: str | None = None


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
    updated_at: datetime | None = None
    user: UserBase | None = None

    model_config = {"from_attributes": True}


class SignOutResponse(BaseModel):
    detail: str

