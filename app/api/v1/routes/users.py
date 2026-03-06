from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.core.rate_limit import RateLimits, limiter
from app.models.user import User
from app.schemas.user import UserOut, UserUpdate, WeeklyProgressOut
from app.services.user_service import UserService
from app.utils.jwt_utils import get_current_user

router = APIRouter()


@router.get("/me", response_model=UserOut)
@limiter.limit(RateLimits.DEFAULT)
async def get_my_user(
    request: Request,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    return await UserService(db).get_user_by_id(current_user.id)


@router.patch("/me", response_model=UserOut)
@limiter.limit(RateLimits.DEFAULT)
async def update_my_user(
    request: Request,
    payload: UserUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    return await UserService(db).update_user(current_user.id, payload)


@router.delete("/me")
@limiter.limit(RateLimits.DEFAULT)
async def delete_my_user(
    request: Request,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    await UserService(db).delete_user(current_user.id)
    return {"status": "deleted", "user_id": current_user.id}


@router.get("/me/progress/weekly", response_model=WeeklyProgressOut)
@limiter.limit(RateLimits.DEFAULT)
async def get_weekly_progress(
    request: Request,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    return await UserService(db).get_weekly_progress(current_user.id)
    
    