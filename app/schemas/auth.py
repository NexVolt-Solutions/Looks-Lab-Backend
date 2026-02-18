"""
Authentication schemas.
Pydantic models for auth requests and responses.
"""
from datetime import datetime

from pydantic import BaseModel, EmailStr

from app.schemas.user import UserOut


# ── Request Schemas ───────────────────────────────────────────────

class OAuthBase(BaseModel):
    """ Added: shared base for OAuth providers"""
    id_token: str
    email: EmailStr | None = None
    name: str | None = None
    picture: str | None = None


class GoogleAuthSchema(OAuthBase):
    """Google OAuth sign-in payload"""
    pass


class AppleAuthSchema(OAuthBase):
    """Apple OAuth sign-in payload"""
    pass


# ── Response Schemas ──────────────────────────────────────────────

class TokenResponse(BaseModel):
    """
    Standard OAuth token response.
    Returned after successful sign-in or token refresh.
    """
    user: UserOut
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int | None = None


class SignOutResponse(BaseModel):
    """Returned after successful sign-out."""
    detail: str


# ── Refresh Token Schemas ─────────────────────────────────────────

class RefreshTokenBase(BaseModel):
    refresh_token: str
    expires_at: datetime


class RefreshTokenCreate(RefreshTokenBase):
    user_id: int
    device_info: str | None = None


class RefreshTokenOut(BaseModel):
    id: int
    user_id: int
    refresh_token: str
    expires_at: datetime
    is_revoked: bool
    device_info: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

