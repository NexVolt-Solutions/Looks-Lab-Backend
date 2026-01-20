from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.enums import AuthProviderEnum
from app.models import User, RefreshToken
from app.schemas.auth import TokenResponse
from app.utils import jwt_utils
from app.utils.jwt_utils import ensure_user_active


def get_or_create_user(email: str, provider: AuthProviderEnum, payload: dict, db: Session) -> User:
    """
    Find or create a user based on email and provider.
    Payload may contain provider-specific fields like name, picture, id_token, sub.
    """
    user = db.query(User).filter(User.email == email).first()
    if user and user.provider and user.provider != provider:
        raise HTTPException(status_code=400, detail="This email is registered with another provider.")

    if not user:
        user = User(
            email=email,
            name=payload.get("name"),
            provider=provider,
            is_verified=True,
            is_active=True,
            profile_image=payload.get("picture"),
            last_google_id_token=payload.get("google_id_token"),
            last_apple_id_token=payload.get("apple_id_token"),
            google_sub=payload.get("google_sub"),
            google_picture=payload.get("google_picture"),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        # Update provider-specific fields
        if payload.get("name") and not user.name:
            user.name = payload.get("name")
        if payload.get("picture"):
            user.profile_image = payload.get("picture")

        # Persist provider (first wins unless empty)
        if not user.provider:
            user.provider = provider

        if provider == AuthProviderEnum.GOOGLE:
            user.google_sub = payload.get("google_sub")
            user.google_picture = payload.get("google_picture")
            user.last_google_id_token = payload.get("google_id_token")
        elif provider == AuthProviderEnum.APPLE:
            user.last_apple_id_token = payload.get("apple_id_token")

        ensure_user_active(user)
        db.commit()

    return user


def issue_tokens(user: User, db: Session) -> TokenResponse:
    """
    Create access + refresh tokens for a user and persist refresh token in DB.
    """
    access_token = jwt_utils.create_access_token({"user_id": str(user.id), "email": user.email})
    refresh_value = jwt_utils.create_refresh_token()
    expires_at = jwt_utils.get_refresh_expiry()

    existing = db.query(RefreshToken).filter(RefreshToken.user_id == user.id).first()
    if existing:
        existing.token = refresh_value
        existing.expires_at = expires_at
    else:
        db.add(RefreshToken(user_id=user.id, token=refresh_value, expires_at=expires_at))
    db.commit()

    return TokenResponse(user=user, access_token=access_token, refresh_token=refresh_value)


def validate_refresh_token(refresh_token: str, db: Session) -> User:
    """
    Validate a refresh token and return the associated user.
    """
    existing = db.query(RefreshToken).filter(RefreshToken.token == refresh_token).first()
    if not existing:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    if existing.expires_at < jwt_utils.get_current_time():
        raise HTTPException(status_code=401, detail="Refresh token expired")

    user = db.query(User).filter(User.id == existing.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


def revoke_refresh_token(refresh_token: str, db: Session) -> None:
    """
    Delete a refresh token to sign out a user.
    """
    token_entry = db.query(RefreshToken).filter(RefreshToken.token == refresh_token).first()
    if not token_entry:
        raise HTTPException(status_code=404, detail="Invalid or missing refresh token")

    db.delete(token_entry)
    db.commit()


