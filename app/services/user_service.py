from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.models.domain import DomainAnswer, DomainQuestion
from app.models.user import User
from app.schemas.user import UserUpdate


class UserService:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_by_id(self, user_id: int) -> User:
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            logger.warning(f"User {user_id} not found")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        await self.db.refresh(user, attribute_names=["subscription"])
        return user

    async def get_user_by_email(self, email: str) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.email == email.lower()))
        user = result.scalar_one_or_none()
        if user:
            await self.db.refresh(user, attribute_names=["subscription"])
        return user

    async def update_user(self, user_id: int, payload: UserUpdate) -> User:
        user = await self.get_user_by_id(user_id)
        changes = []

        fields = ["name", "age", "gender", "profile_image", "notifications_enabled"]
        for field in fields:
            new_val = getattr(payload, field)
            if new_val is not None and new_val != getattr(user, field):
                setattr(user, field, new_val)
                changes.append(field)

        if changes:
            user.updated_at = datetime.now(timezone.utc)
            await self.db.commit()
            await self.db.refresh(user, attribute_names=["subscription"])
            logger.info(f"Updated user {user_id}: {', '.join(changes)}")

        return user

    async def delete_user(self, user_id: int) -> None:
        user = await self.get_user_by_id(user_id)
        email = user.email
        await self.db.delete(user)
        await self.db.commit()
        logger.info(f"Deleted user {user_id} ({email})")

    async def get_weekly_progress(self, user_id: int) -> dict:
        today = datetime.now(timezone.utc).date()
        monday = today - timedelta(days=today.weekday())
        week_dates = [monday + timedelta(days=i) for i in range(7)]
        day_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

        total_result = await self.db.execute(select(func.count(DomainQuestion.id)))
        total_questions = total_result.scalar() or 1

        result = await self.db.execute(
            select(DomainAnswer)
            .where(DomainAnswer.user_id == user_id)
            .order_by(DomainAnswer.completed_at.asc())
        )
        all_answers = result.scalars().all()

        days = []
        scores = []

        for date, label in zip(week_dates, day_labels):
            end_of_day = datetime.combine(
                date + timedelta(days=1),
                datetime.min.time()
            ).replace(tzinfo=timezone.utc)

            answered_count = sum(
                1 for a in all_answers
                if a.completed_at and a.completed_at < end_of_day
            )
            score = min(round((answered_count / total_questions) * 100, 1), 100.0)

            days.append({"day": label, "date": date.strftime("%Y-%m-%d"), "score": score})
            scores.append(score)

        return {
            "user_id": user_id,
            "labels": day_labels,
            "scores": scores,
            "days": days,
            "week_average": round(sum(scores) / len(scores), 1) if scores else 0.0
        }

