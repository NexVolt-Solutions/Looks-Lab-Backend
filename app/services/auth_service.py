"""
Authentication service layer.
Handles OAuth authentication, token management, and user creation.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from app.enums import AuthProviderEnum
from app.models.user import User
from app.models.refresh_token import RefreshToken
from app.schemas.auth import TokenResponse
from app.utils.jwt_utils import (
    create_access_token,
    create_refresh_token,
    get_refresh_expiry,
    get_current_time,
    ensure_user_active
)
from app.core.logging import logger


class AuthService:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_user(
            self,
            email: str,
            provider: AuthProviderEnum,
            payload: dict
    ) -> User:
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
        else:
            user = await self._update_existing_user(user, provider, payload)
            logger.info(f"Updated user: {email} via {provider}")

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
            google_sub=payload.get("google_sub"),
            google_picture=payload.get("google_picture"),
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
        if payload.get("name") and not user.name:
            user.name = payload.get("name")

        if payload.get("picture"):
            user.profile_image = payload.get("picture")

        if not user.provider:
            user.provider = provider

        if provider == AuthProviderEnum.GOOGLE:
            user.google_sub = payload.get("google_sub")
            user.google_picture = payload.get("google_picture")

        ensure_user_active(user)

        await self.db.commit()
        await self.db.refresh(user)

        return user

    async def issue_tokens(self, user: User) -> TokenResponse:
        access_token = create_access_token({
            "user_id": str(user.id),
            "email": user.email
        })

        refresh_value = create_refresh_token()
        expires_at = get_refresh_expiry()

        result = await self.db.execute(
            select(RefreshToken).where(RefreshToken.user_id == user.id)
        )
        existing_token = result.scalar_one_or_none()

        if existing_token:
            existing_token.token = refresh_value
            existing_token.expires_at = expires_at
            existing_token.updated_at = get_current_time()
            logger.info(f"Updated refresh token for user {user.id}")
        else:
            new_token = RefreshToken(
                user_id=user.id,
                token=refresh_value,
                expires_at=expires_at
            )
            self.db.add(new_token)
            logger.info(f"Created refresh token for user {user.id}")

        await self.db.commit()

        return TokenResponse(
            user=user,
            access_token=access_token,
            refresh_token=refresh_value
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

        if token_record.expires_at < get_current_time():
            logger.warning(f"Expired refresh token for user {token_record.user_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token expired"
            )

        result = await self.db.execute(
            select(User).where(User.id == token_record.user_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            logger.error(f"User {token_record.user_id} not found for valid refresh token")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

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

        user_id = token_record.user_id
        await self.db.delete(token_record)
        await self.db.commit()

        logger.info(f"Revoked refresh token for user {user_id}")

