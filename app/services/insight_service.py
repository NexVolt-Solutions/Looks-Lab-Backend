from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.models.insight import Insight
from app.schemas.insight import InsightCreate, InsightUpdate


class InsightService:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_or_update_insight(self, payload: InsightCreate) -> Insight:
        result = await self.db.execute(
            select(Insight).where(
                Insight.user_id == payload.user_id,
                Insight.category == payload.category,
            )
            .order_by(Insight.created_at.desc())
            .limit(1)
        )
        existing = result.scalars().first()

        if existing:
            existing.content = payload.content
            existing.source = payload.source
            existing.score = payload.score
            existing.is_read = False
            existing.updated_at = datetime.now(timezone.utc)
            await self.db.commit()
            await self.db.refresh(existing)
            logger.info(f"Updated {payload.category} insight for user {payload.user_id} — score: {payload.score}")
            return existing

        insight = Insight(
            user_id=payload.user_id,
            category=payload.category,
            content=payload.content,
            source=payload.source,
            score=payload.score,
            is_read=False,
        )
        self.db.add(insight)
        await self.db.commit()
        await self.db.refresh(insight)
        logger.info(f"Created {payload.category} insight for user {payload.user_id} — score: {payload.score}")
        return insight

    async def get_insight(self, insight_id: int, user_id: int) -> Insight:
        result = await self.db.execute(select(Insight).where(Insight.id == insight_id))
        insight = result.scalar_one_or_none()

        if not insight:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Insight not found")
        if insight.user_id != user_id:
            logger.warning(f"User {user_id} attempted to access insight {insight_id} owned by {insight.user_id}")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this insight")

        return insight

    async def get_user_insights(
        self,
        user_id: int,
        domain: Optional[str] = None,
        unread_only: bool = False,
    ) -> list[Insight]:
        query = select(Insight).where(Insight.user_id == user_id).order_by(Insight.created_at.desc())

        if domain:
            query = query.where(Insight.category == domain)
        if unread_only:
            query = query.where(Insight.is_read == False)  # noqa: E712

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_insight_by_domain(self, user_id: int, domain: str) -> Optional[Insight]:
        result = await self.db.execute(
            select(Insight).where(
                Insight.user_id == user_id,
                Insight.category == domain,
            )
            .order_by(Insight.created_at.desc())
            .limit(1)
        )
        return result.scalars().first()

    async def mark_as_read(self, insight_id: int, user_id: int) -> Insight:
        insight = await self.get_insight(insight_id, user_id)
        if insight.is_read:
            return insight

        insight.is_read = True
        await self.db.commit()
        await self.db.refresh(insight)
        logger.info(f"Marked insight {insight_id} as read for user {user_id}")
        return insight

    async def update_insight(self, insight_id: int, user_id: int, payload: InsightUpdate) -> Insight:
        insight = await self.get_insight(insight_id, user_id)

        if payload.content is not None:
            insight.content = payload.content
        if payload.source is not None:
            insight.source = payload.source
        if payload.category is not None:
            insight.category = payload.category
        if payload.score is not None:
            insight.score = payload.score
        if payload.is_read is not None:
            insight.is_read = payload.is_read

        await self.db.commit()
        await self.db.refresh(insight)
        logger.info(f"Updated insight {insight_id} for user {user_id}")
        return insight

    async def get_weekly_scores(self, user_id: int) -> dict:
        result = await self.db.execute(
            select(Insight).where(Insight.user_id == user_id)
            .order_by(Insight.created_at.desc())
        )
        insights = result.scalars().all()

        # Deduplicate — keep latest insight per domain
        seen = {}
        for insight in insights:
            domain = str(insight.category)
            if domain not in seen:
                seen[domain] = insight

        domain_scores = {}
        for domain, insight in seen.items():
            score = insight.score or 0.0
            domain_scores[domain] = {
                "domain": domain,
                "score": round(score, 1),
                "icon_url": _DOMAIN_ICONS.get(domain),
                "has_data": insight.score is not None,
            }

        return domain_scores


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

