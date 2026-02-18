"""
User service layer.
Handles user profile operations (CRUD) and progress tracking.
"""
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from fastapi import HTTPException, status

from app.models.user import User
from app.models.domain import DomainAnswer
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

    # ==================== NEW: WEEKLY PROGRESS ====================

    async def get_weekly_progress(self, user_id: int) -> dict:
        """
        Calculate weekly progress from domain question completion.

        Logic:
        - Get last 7 days (Mon-Sun of current week)
        - For each day, count how many domain answers
          were submitted that day
        - Calculate score as percentage of total
          domain questions answered up to that day

        Args:
            user_id: User ID

        Returns:
            Weekly progress data for chart display
        """
        # Get current week's Mon-Sun dates
        today = datetime.now(timezone.utc).date()
        # Get Monday of current week
        monday = today - timedelta(days=today.weekday())
        week_dates = [monday + timedelta(days=i) for i in range(7)]
        day_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

        # Get total domain questions available (for score calculation)
        from app.models.domain import DomainQuestion
        total_result = await self.db.execute(
            select(func.count(DomainQuestion.id))
        )
        total_questions = total_result.scalar() or 1  # Avoid division by zero

        # Get all user's domain answers with their completion dates
        result = await self.db.execute(
            select(DomainAnswer)
            .where(DomainAnswer.user_id == user_id)
            .order_by(DomainAnswer.completed_at.asc())
        )
        all_answers = result.scalars().all()

        # Build daily scores
        days = []
        scores = []

        for i, (date, label) in enumerate(zip(week_dates, day_labels)):
            # Count answers completed up to end of this day
            # This gives cumulative progress
            end_of_day = datetime.combine(
                date + timedelta(days=1),
                datetime.min.time()
            ).replace(tzinfo=timezone.utc)

            answers_up_to_day = [
                a for a in all_answers
                if a.completed_at and a.completed_at < end_of_day
            ]

            # Calculate score as percentage of total questions
            score = round(
                (len(answers_up_to_day) / total_questions) * 100, 1
            )
            # Cap at 100
            score = min(score, 100.0)

            days.append({
                "day": label,
                "date": date.strftime("%Y-%m-%d"),
                "score": score
            })
            scores.append(score)

        # Calculate week average
        week_average = round(sum(scores) / len(scores), 1) if scores else 0.0

        logger.info(f"Calculated weekly progress for user {user_id}")

        return {
            "user_id": user_id,
            "labels": day_labels,
            "scores": scores,
            "days": days,
            "week_average": week_average
        }

