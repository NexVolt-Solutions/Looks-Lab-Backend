from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.core.rate_limit import RateLimits, limiter
from app.models.user import User
from app.schemas.insight import InsightCreate, InsightUpdate, InsightOut, InsightListOut
from app.services.insight_service import InsightService
from app.utils.jwt_utils import get_current_user

router = APIRouter()


@router.get("/me", response_model=InsightListOut)
async def get_my_insights(
    request: Request,
    domain: str | None = Query(None),
    unread_only: bool = Query(False),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    insights = await InsightService(db).get_user_insights(
        user_id=current_user.id,
        domain=domain,
        unread_only=unread_only,
    )
    return InsightListOut(
        insights=insights,
        total=len(insights),
        unread_count=sum(1 for i in insights if not i.is_read)
    )


@router.post("/", response_model=InsightOut)
@limiter.limit(RateLimits.DEFAULT)
async def create_insight(
    request: Request,
    payload: InsightCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    payload.user_id = current_user.id
    return await InsightService(db).create_insight(payload)


@router.get("/{insight_id}", response_model=InsightOut)
async def get_insight(
    insight_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    return await InsightService(db).get_insight(insight_id, current_user.id)


@router.patch("/{insight_id}/read", response_model=InsightOut)
async def mark_insight_read(
    insight_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    return await InsightService(db).mark_as_read(insight_id, current_user.id)


@router.patch("/{insight_id}", response_model=InsightOut)
async def update_insight(
    insight_id: int,
    payload: InsightUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    return await InsightService(db).update_insight(insight_id, current_user.id, payload)


@router.delete("/{insight_id}")
async def delete_insight(
    insight_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    await InsightService(db).delete_insight(insight_id, current_user.id)
    return {"status": "deleted", "insight_id": insight_id}

