"""
Insight service layer.
Handles AI-generated insight operations.
"""
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.models.insight import Insight
from app.schemas.insight import InsightCreate, InsightUpdate


class InsightService:

    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Create ────────────────────────────────────────────────────

    async def create_insight(self, payload: InsightCreate) -> Insight:
        """Create a new insight for a user."""
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

    # ── Retrieval ─────────────────────────────────────────────────

    async def get_insight(self, insight_id: int, user_id: int) -> Insight:
        """Get insight by ID with ownership check."""
        result = await self.db.execute(
            select(Insight).where(Insight.id == insight_id)
        )
        insight = result.scalar_one_or_none()

        if not insight:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Insight not found"
            )

        if insight.user_id != user_id:
            logger.warning(
                f"User {user_id} attempted to access insight "
                f"{insight_id} owned by {insight.user_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this insight"
            )

        return insight

    async def get_user_insights(
        self,
        user_id: int,
        domain: str | None = None,
        unread_only: bool = False,
    ) -> list[Insight]:
        """
        Get all insights for a user with optional filters.

        Args:
            user_id: User ID
            domain: Filter by category/domain (e.g. skincare, haircare)
            unread_only: If True, return only unread insights
        """
        query = (
            select(Insight)
            .where(Insight.user_id == user_id)
            .order_by(Insight.created_at.desc())
        )

        if domain:
            query = query.where(Insight.category == domain)

        if unread_only:
            query = query.where(Insight.is_read == False)   # noqa: E712

        result = await self.db.execute(query)
        return list(result.scalars().all())

    # ── Update ────────────────────────────────────────────────────

    async def mark_as_read(self, insight_id: int, user_id: int) -> Insight:
        """Mark insight as read. No-op if already read."""
        insight = await self.get_insight(insight_id, user_id)

        if insight.is_read:
            return insight  # Already read — skip unnecessary DB write

        insight.is_read = True

        await self.db.commit()
        await self.db.refresh(insight)

        logger.info(f"Marked insight {insight_id} as read for user {user_id}")
        return insight

    async def update_insight(
        self,
        insight_id: int,
        user_id: int,
        payload: InsightUpdate
    ) -> Insight:
        """Update insight content, source, category or read status."""
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

    # ── Delete ────────────────────────────────────────────────────

    async def delete_insight(self, insight_id: int, user_id: int) -> None:
        """Delete an insight."""
        insight = await self.get_insight(insight_id, user_id)

        await self.db.delete(insight)
        await self.db.commit()

        logger.info(f"Deleted insight {insight_id} for user {user_id}")

