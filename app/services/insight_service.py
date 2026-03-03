from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.models.insight import Insight
from app.schemas.insight import InsightCreate, InsightUpdate


class InsightService:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_insight(self, payload: InsightCreate) -> Insight:
        insight = Insight(
            user_id=payload.user_id,
            category=payload.category,
            content=payload.content,
            source=payload.source,
            is_read=False,
        )

        self.db.add(insight)
        await self.db.commit()
        await self.db.refresh(insight)

        logger.info(f"Created {payload.category} insight for user {payload.user_id}")
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
        if payload.is_read is not None:
            insight.is_read = payload.is_read

        await self.db.commit()
        await self.db.refresh(insight)

        logger.info(f"Updated insight {insight_id} for user {user_id}")
        return insight

    async def delete_insight(self, insight_id: int, user_id: int) -> None:
        insight = await self.get_insight(insight_id, user_id)
        await self.db.delete(insight)
        await self.db.commit()
        logger.info(f"Deleted insight {insight_id} for user {user_id}")

