from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.enums import DomainEnum
from app.models.insight import Insight
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
        """
        Returns weekly progress scores per domain.

        Each domain shows the AI score saved when the user completed
        their domain questions. Only purchased domains have a real score.
        Unpurchased domains show 0.0 with has_data=False.

        The weekly_average is calculated only from domains that have data.
        """
        # Fetch all insights for this user (one per domain max)
        result = await self.db.execute(
            select(Insight).where(Insight.user_id == user_id)
        )
        insights = {str(i.category): i for i in result.scalars().all()}

        # Build score for every domain — 0 if not purchased/completed
        domains = []
        scores_with_data = []

        for domain in DomainEnum.values():
            insight = insights.get(domain)
            if insight and insight.score is not None:
                score = round(insight.score, 1)
                has_data = True
                scores_with_data.append(score)
            else:
                score = 0.0
                has_data = False

            domains.append({
                "domain":   domain,
                "score":    score,
                "has_data": has_data,
                "icon_url": _DOMAIN_ICONS.get(domain),
            })

        weekly_average = round(sum(scores_with_data) / len(scores_with_data), 1) if scores_with_data else 0.0

        return {
            "user_id":        user_id,
            "domains":        domains,
            "weekly_average": weekly_average,
        }


_DOMAIN_ICONS = {
    "skincare":  "https://api.lookslabai.com/static/icons/SkinCare.jpg",
    "haircare":  "https://api.lookslabai.com/static/icons/Hair.png",
    "workout":   "https://api.lookslabai.com/static/icons/Workout.jpg",
    "diet":      "https://api.lookslabai.com/static/icons/Diet.jpg",
    "facial":    "https://api.lookslabai.com/static/icons/Facial.jpg",
    "fashion":   "https://api.lookslabai.com/static/icons/Fashion.png",
    "height":    "https://api.lookslabai.com/static/icons/Height.jpg",
    "quit_porn": "https://api.lookslabai.com/static/icons/QuitPorn.jpg",
}

