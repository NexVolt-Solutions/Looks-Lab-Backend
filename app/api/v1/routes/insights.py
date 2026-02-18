"""
Insights routes.
Handles AI-generated insight operations (CRUD).
"""
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.core.rate_limit import RateLimits, limiter
from app.models.user import User
from app.schemas.insight import (
    InsightCreate,
    InsightUpdate,
    InsightOut,
    InsightListOut,
)
from app.services.insight_service import InsightService
from app.utils.jwt_utils import get_current_user

router = APIRouter()


# ── Collection Routes (must be before /{insight_id}) ─────────────

@router.get("/me", response_model=InsightListOut)
async def get_my_insights(
    request: Request,  # noqa: ARG001
    domain: str | None = Query(None),
    unread_only: bool = Query(False),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get all insights for current user with unread count.

    Query params:
        domain: Filter by domain (skincare, haircare, etc.)
        unread_only: If true, return only unread insights
    """
    insight_service = InsightService(db)
    insights = await insight_service.get_user_insights(
        user_id=current_user.id,
        domain=domain,
        unread_only=unread_only,
    )


    unread_count = sum(1 for i in insights if not i.is_read)

    return InsightListOut(
        insights=insights,
        total=len(insights),
        unread_count=unread_count
    )


@router.post("/", response_model=InsightOut)
@limiter.limit(RateLimits.DEFAULT)
async def create_insight(
    request: Request,  # noqa: ARG001
    payload: InsightCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new insight for current user."""
    insight_service = InsightService(db)
    payload.user_id = current_user.id
    return await insight_service.create_insight(payload)


# ── Single Resource Routes ────────────────────────────────────────

@router.get("/{insight_id}", response_model=InsightOut)
async def get_insight(
    request: Request,  # noqa: ARG001
    insight_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific insight by ID."""
    insight_service = InsightService(db)
    return await insight_service.get_insight(insight_id, current_user.id)


@router.patch("/{insight_id}/read", response_model=InsightOut)
async def mark_insight_read(
    request: Request,  # noqa: ARG001
    insight_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    """Mark an insight as read."""
    insight_service = InsightService(db)
    return await insight_service.mark_as_read(insight_id, current_user.id)


@router.patch("/{insight_id}", response_model=InsightOut)
async def update_insight(
    request: Request,  # noqa: ARG001
    insight_id: int,
    payload: InsightUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    """Update an insight."""
    insight_service = InsightService(db)
    return await insight_service.update_insight(insight_id, current_user.id, payload)


@router.delete("/{insight_id}")
async def delete_insight(
    request: Request,  # noqa: ARG001
    insight_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    """Delete an insight."""
    insight_service = InsightService(db)
    await insight_service.delete_insight(insight_id, current_user.id)

    return {
        "status": "deleted",
        "insight_id": insight_id,
        "message": "Insight deleted successfully"
    }

