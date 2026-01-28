"""
Insights routes.
Handles AI-generated insight operations (CRUD).
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.models.user import User
from app.schemas.insight import InsightCreate, InsightUpdate, InsightOut
from app.services.insight_service import InsightService
from app.utils.jwt_utils import get_current_user

router = APIRouter()


@router.post("/", response_model=InsightOut)
async def create_insight(
        payload: InsightCreate,
        db: AsyncSession = Depends(get_async_db),
        current_user: User = Depends(get_current_user),
):
    insight_service = InsightService(db)

    payload.user_id = current_user.id

    return await insight_service.create_insight(payload)


@router.get("/{insight_id}", response_model=InsightOut)
async def get_insight(
        insight_id: int,
        db: AsyncSession = Depends(get_async_db),
        current_user: User = Depends(get_current_user),
):
    insight_service = InsightService(db)
    return await insight_service.get_insight(insight_id, current_user.id)


@router.get("/me", response_model=list[InsightOut])
async def get_my_insights(
        db: AsyncSession = Depends(get_async_db),
        current_user: User = Depends(get_current_user),
):
    insight_service = InsightService(db)
    return await insight_service.get_user_insights(current_user.id)


@router.patch("/{insight_id}", response_model=InsightOut)
async def update_insight(
        insight_id: int,
        payload: InsightUpdate,
        db: AsyncSession = Depends(get_async_db),
        current_user: User = Depends(get_current_user),
):
    insight_service = InsightService(db)
    return await insight_service.update_insight(insight_id, current_user.id, payload)


@router.delete("/{insight_id}")
async def delete_insight(
        insight_id: int,
        db: AsyncSession = Depends(get_async_db),
        current_user: User = Depends(get_current_user),
):
    insight_service = InsightService(db)
    await insight_service.delete_insight(insight_id, current_user.id)

    return {
        "status": "deleted",
        "insight_id": insight_id,
        "message": "Insight deleted successfully"
    }

