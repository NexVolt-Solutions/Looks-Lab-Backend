"""
User service layer.
Handles user profile operations (CRUD).
"""
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from app.models.user import User
from app.schemas.user import UserUpdate
from app.core.logging import logger


class UserService:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_by_id(self, user_id: int) -> User:
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            logger.warning(f"User {user_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        return user

    async def get_user_by_email(self, email: str) -> User | None:
        result = await self.db.execute(select(User).where(User.email == email.lower()))
        return result.scalar_one_or_none()

    async def update_user(self, user_id: int, payload: UserUpdate) -> User:
        user = await self.get_user_by_id(user_id)

        changes = []

        if payload.name is not None and payload.name != user.name:
            user.name = payload.name
            changes.append("name")

        if payload.age is not None and payload.age != user.age:
            user.age = payload.age
            changes.append("age")

        if payload.gender is not None and payload.gender != user.gender:
            user.gender = payload.gender
            changes.append("gender")

        if payload.profile_image is not None and payload.profile_image != user.profile_image:
            user.profile_image = payload.profile_image
            changes.append("profile_image")

        if payload.notifications_enabled is not None and payload.notifications_enabled != user.notifications_enabled:
            user.notifications_enabled = payload.notifications_enabled
            changes.append("notifications_enabled")

        if changes:
            user.updated_at = datetime.now(timezone.utc)
            await self.db.commit()
            await self.db.refresh(user)
            logger.info(f"Updated user {user_id}: {', '.join(changes)}")
        else:
            logger.debug(f"No changes for user {user_id}")

        return user

    async def delete_user(self, user_id: int) -> None:
        user = await self.get_user_by_id(user_id)
        email = user.email

        await self.db.delete(user)
        await self.db.commit()

        logger.info(f"Deleted user {user_id} ({email})")

    def check_user_active(self, user: User) -> None:
        if not user.is_active:
            logger.warning(f"Inactive user {user.id} attempted action")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive"
            )

    def check_user_verified(self, user: User) -> None:
        if not user.is_verified:
            logger.warning(f"Unverified user {user.id} attempted action")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Email verification required"
            )

