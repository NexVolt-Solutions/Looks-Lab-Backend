from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.core.rate_limit import RateLimits, limiter
from app.models.user import User
from app.schemas.insight import InsightOut, InsightListOut
from app.services.insight_service import InsightService
from app.utils.jwt_utils import get_current_user

router = APIRouter()


@router.get("/me", response_model=InsightListOut)
@limiter.limit(RateLimits.DEFAULT)
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
        unread_count=sum(1 for i in insights if not i.is_read),
    )


@router.get("/me/domain/{domain}", response_model=InsightOut)
@limiter.limit(RateLimits.DEFAULT)
async def get_my_domain_insight(
    request: Request,
    domain: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    insight = await InsightService(db).get_insight_by_domain(current_user.id, domain)
    if not insight:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No insight found for domain '{domain}'")
    return insight


@router.get("/{insight_id}", response_model=InsightOut)
@limiter.limit(RateLimits.DEFAULT)
async def get_insight(
    request: Request,
    insight_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    return await InsightService(db).get_insight(insight_id, current_user.id)


@router.patch("/{insight_id}/read", response_model=InsightOut)
@limiter.limit(RateLimits.DEFAULT)
async def mark_insight_read(
    request: Request,
    insight_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    return await InsightService(db).mark_as_read(insight_id, current_user.id)
    
    