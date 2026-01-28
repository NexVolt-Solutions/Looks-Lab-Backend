"""
Insight service layer.
Handles AI-generated insight operations.
"""
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from app.models.insight import Insight
from app.schemas.insight import InsightCreate, InsightUpdate
from app.core.logging import logger


class InsightService:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_insight(self, payload: InsightCreate) -> Insight:
        insight = Insight(
            user_id=payload.user_id,
            category=payload.category,
            content=payload.content,
            source=payload.source,
            created_at=datetime.now(timezone.utc),
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
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Insight not found"
            )

        if insight.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this insight"
            )

        return insight

    async def get_user_insights(self, user_id: int) -> list[Insight]:
        result = await self.db.execute(select(Insight).where(Insight.user_id == user_id))
        return list(result.scalars().all())

    async def update_insight(self, insight_id: int, user_id: int, payload: InsightUpdate) -> Insight:
        insight = await self.get_insight(insight_id, user_id)

        if payload.content is not None:
            insight.content = payload.content
        if payload.source is not None:
            insight.source = payload.source
        if payload.category is not None:
            insight.category = payload.category

        insight.updated_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(insight)

        logger.info(f"Updated insight {insight_id} for user {user_id}")
        return insight

    async def delete_insight(self, insight_id: int, user_id: int) -> None:
        insight = await self.get_insight(insight_id, user_id)

        await self.db.delete(insight)
        await self.db.commit()

        logger.info(f"Deleted insight {insight_id} for user {user_id}")

