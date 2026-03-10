from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import logger
from app.enums import AuthProviderEnum
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.schemas.auth import TokenResponse
from app.schemas.user import UserOut
from app.utils.jwt_utils import (
    create_access_token,
    create_refresh_token,
    get_refresh_expiry,
    get_current_time,
    ensure_user_active,
)


class AuthService:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_user(
        self, email: str, provider: AuthProviderEnum, payload: dict
    ) -> tuple[User, bool]:
        """Returns (user, is_new_user)"""
        email = email.lower().strip()

        result = await self.db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if user and user.provider and user.provider != provider:
            logger.warning(f"Email {email} attempted login with {provider} but registered with {user.provider}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"This email is registered with {user.provider}. Please use {user.provider} to sign in."
            )

        if not user:
            user = await self._create_new_user(email, provider, payload)
            logger.info(f"Created new user: {email} via {provider}")
            return user, True
        else:
            user = await self._update_existing_user(user, provider, payload)
            logger.info(f"Updated existing user: {email} via {provider}")
            return user, False

    async def _create_new_user(self, email: str, provider: AuthProviderEnum, payload: dict) -> User:
        user = User(
            email=email,
            name=payload.get("name"),
            provider=provider,
            is_verified=True,
            is_active=True,
            profile_image=payload.get("picture"),
            google_sub=payload.get("google_sub"),
            google_picture=payload.get("google_picture"),
            last_google_id_token=payload.get("last_google_id_token"),
            apple_sub=payload.get("apple_sub"),
            last_apple_id_token=payload.get("last_apple_id_token"),
        )

        try:
            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to create user {email}: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create account")

        return user

    async def _update_existing_user(self, user: User, provider: AuthProviderEnum, payload: dict) -> User:
        if payload.get("name") and not user.name:
            user.name = payload.get("name")
        if payload.get("picture"):
            user.profile_image = payload.get("picture")
        if not user.provider:
            user.provider = provider

        if provider == AuthProviderEnum.GOOGLE:
            user.google_sub = payload.get("google_sub")
            user.google_picture = payload.get("google_picture")
            user.last_google_id_token = payload.get("last_google_id_token")
        elif provider == AuthProviderEnum.APPLE:
            user.apple_sub = payload.get("apple_sub")
            user.last_apple_id_token = payload.get("last_apple_id_token")

        ensure_user_active(user)

        try:
            await self.db.commit()
            await self.db.refresh(user)
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to update user {user.email}: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update account")

        return user

    async def update_last_login(self, user_id: int) -> None:
        try:
            user = await self.db.get(User, user_id)
            if user:
                user.last_login = datetime.now(timezone.utc)
                await self.db.commit()
        except Exception as e:
            logger.error(f"Failed to update last_login for user {user_id}: {e}")

    async def issue_tokens(
        self, user: User, is_new_user: bool = False, device_info: Optional[str] = None
    ) -> TokenResponse:
        access_token = create_access_token({
            "user_id": str(user.id),
            "email": user.email,
            "provider": user.provider,
        })

        refresh_value = create_refresh_token()
        expires_at = get_refresh_expiry()

        result = await self.db.execute(select(RefreshToken).where(RefreshToken.user_id == user.id))
        existing_token = result.scalar_one_or_none()

        try:
            if existing_token:
                existing_token.token = refresh_value
                existing_token.expires_at = expires_at
                existing_token.is_revoked = False
                existing_token.device_info = device_info
            else:
                self.db.add(RefreshToken(
                    user_id=user.id,
                    token=refresh_value,
                    expires_at=expires_at,
                    is_revoked=False,
                    device_info=device_info,
                ))
            await self.db.commit()
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to issue tokens for user {user.id}: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to issue tokens")

        await self.db.refresh(user, attribute_names=["updated_at", "subscription"])

        return TokenResponse(
            user=UserOut.model_validate(user),
            access_token=access_token,
            refresh_token=refresh_value,
            token_type="bearer",
            expires_in=settings.JWT_EXPIRATION_MINUTES * 60,
            is_new_user=is_new_user,
        )

    async def validate_refresh_token(self, refresh_token: str) -> User:
        result = await self.db.execute(select(RefreshToken).where(RefreshToken.token == refresh_token))
        token_record = result.scalar_one_or_none()

        if not token_record:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
        if token_record.is_revoked:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token has been revoked")
        if token_record.expires_at < get_current_time():
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired")

        result = await self.db.execute(select(User).where(User.id == token_record.user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        ensure_user_active(user)
        return user

    async def revoke_refresh_token(self, refresh_token: str) -> None:
        result = await self.db.execute(select(RefreshToken).where(RefreshToken.token == refresh_token))
        token_record = result.scalar_one_or_none()

        if not token_record:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid or missing refresh token")

        token_record.is_revoked = True
        try:
            await self.db.commit()
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to revoke refresh token for user {token_record.user_id}: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to revoke token")

        logger.info(f"Revoked refresh token for user {token_record.user_id}")
        
        