"""
Authentication service layer.
Handles OAuth authentication, token management, and user creation.
"""
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import logger
from app.enums import AuthProviderEnum
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.schemas.auth import TokenResponse
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

    # ── User Management ───────────────────────────────────────────

    async def get_or_create_user(
        self,
        email: str,
        provider: AuthProviderEnum,
        payload: dict
    ) -> User:
        email = email.lower().strip()

        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()

        # Provider mismatch check
        if user and user.provider and user.provider != provider:
            logger.warning(
                f"Email {email} attempted login with {provider} "
                f"but registered with {user.provider}"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"This email is registered with {user.provider}. "
                    f"Please use {user.provider} to sign in."
                )
            )

        if not user:
            user = await self._create_new_user(email, provider, payload)
            logger.info(f"Created new user: {email} via {provider}")
        else:
            user = await self._update_existing_user(user, provider, payload)
            logger.info(f"Updated existing user: {email} via {provider}")

        return user

    async def _create_new_user(
        self,
        email: str,
        provider: AuthProviderEnum,
        payload: dict
    ) -> User:
        user = User(
            email=email,
            name=payload.get("name"),
            provider=provider,
            is_verified=True,
            is_active=True,
            profile_image=payload.get("picture"),

            # ── Google fields ──────────────────────────────────
            google_sub=payload.get("google_sub"),
            google_picture=payload.get("google_picture"),
            last_google_id_token=payload.get("last_google_id_token"),

            # ── Apple fields ───────────────────────────────────
            apple_sub=payload.get("apple_sub"),
            last_apple_id_token=payload.get("last_apple_id_token"),
        )

        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        return user

    async def _update_existing_user(
        self,
        user: User,
        provider: AuthProviderEnum,
        payload: dict
    ) -> User:
        # Update name only if not set
        if payload.get("name") and not user.name:
            user.name = payload.get("name")

        # Always update profile picture
        if payload.get("picture"):
            user.profile_image = payload.get("picture")

        # Set provider if missing
        if not user.provider:
            user.provider = provider

        # ── Google specific updates ────────────────────────────
        if provider == AuthProviderEnum.GOOGLE:
            user.google_sub = payload.get("google_sub")
            user.google_picture = payload.get("google_picture")
            user.last_google_id_token = payload.get("last_google_id_token")

        # ── Apple specific updates ─────────────────────────────
        #  Added: was completely missing
        if provider == AuthProviderEnum.APPLE:
            user.apple_sub = payload.get("apple_sub")
            user.last_apple_id_token = payload.get("last_apple_id_token")

        ensure_user_active(user)

        await self.db.commit()
        await self.db.refresh(user)

        return user

    async def update_last_login(self, user_id: int) -> None:
        """
         Added: Update user's last_login timestamp.
        Called after every successful authentication.
        Non-critical — errors are logged but not raised.
        """
        try:
            user = await self.db.get(User, user_id)
            if user:
                user.last_login = datetime.now(timezone.utc)
                await self.db.commit()
        except Exception as e:
            logger.error(f"Failed to update last_login for user {user_id}: {e}")
            # Don't raise — last_login update is non-critical

    # ── Token Management ──────────────────────────────────────────

    async def issue_tokens(
        self,
        user: User,
        device_info: str | None = None
    ) -> TokenResponse:
        access_token = create_access_token({
            "user_id": str(user.id),
            "email": user.email
        })

        refresh_value = create_refresh_token()
        expires_at = get_refresh_expiry()

        # Check for existing token
        result = await self.db.execute(
            select(RefreshToken).where(RefreshToken.user_id == user.id)
        )
        existing_token = result.scalar_one_or_none()

        if existing_token:
            existing_token.token = refresh_value
            existing_token.expires_at = expires_at
            existing_token.is_revoked = False
            existing_token.device_info = device_info
            logger.info(f"Rotated refresh token for user {user.id}")
        else:
            new_token = RefreshToken(
                user_id=user.id,
                token=refresh_value,
                expires_at=expires_at,
                is_revoked=False,
                device_info=device_info,
            )
            self.db.add(new_token)
            logger.info(f"Created refresh token for user {user.id}")

        await self.db.commit()


        expires_in = settings.JWT_EXPIRATION_MINUTES * 60

        return TokenResponse(
            user=user,
            access_token=access_token,
            refresh_token=refresh_value,
            token_type="bearer",
            expires_in=expires_in,
        )

    async def validate_refresh_token(self, refresh_token: str) -> User:
        result = await self.db.execute(
            select(RefreshToken).where(RefreshToken.token == refresh_token)
        )
        token_record = result.scalar_one_or_none()

        if not token_record:
            logger.warning("Invalid refresh token attempted")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )


        if token_record.is_revoked:
            logger.warning(
                f"Revoked refresh token used for user {token_record.user_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has been revoked"
            )

        # Check expiry
        if token_record.expires_at < get_current_time():
            logger.warning(
                f"Expired refresh token for user {token_record.user_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token expired"
            )

        # Get user
        result = await self.db.execute(
            select(User).where(User.id == token_record.user_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            logger.error(
                f"User {token_record.user_id} not found for valid refresh token"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        ensure_user_active(user)

        logger.info(f"Validated refresh token for user {user.id}")
        return user

    async def revoke_refresh_token(self, refresh_token: str) -> None:
        result = await self.db.execute(
            select(RefreshToken).where(RefreshToken.token == refresh_token)
        )
        token_record = result.scalar_one_or_none()

        if not token_record:
            logger.warning("Attempted to revoke non-existent refresh token")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invalid or missing refresh token"
            )

        #  Fixed: mark as revoked instead of deleting — keeps audit trail
        token_record.is_revoked = True
        await self.db.commit()

        logger.info(f"Revoked refresh token for user {token_record.user_id}")

