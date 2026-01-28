"""
User routes.
Handles user profile operations (get, update, delete).
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.models.user import User
from app.schemas.user import UserOut, UserUpdate
from app.services.user_service import UserService
from app.utils.jwt_utils import get_current_user

router = APIRouter()


@router.get("/me", response_model=UserOut)
async def get_my_user(
        db: AsyncSession = Depends(get_async_db),
        current_user: User = Depends(get_current_user),
):
    user_service = UserService(db)
    return await user_service.get_user_by_id(current_user.id)


@router.patch("/me", response_model=UserOut)
async def update_my_user(
        payload: UserUpdate,
        db: AsyncSession = Depends(get_async_db),
        current_user: User = Depends(get_current_user),
):
    user_service = UserService(db)
    return await user_service.update_user(current_user.id, payload)


@router.delete("/me")
async def delete_my_user(
        db: AsyncSession = Depends(get_async_db),
        current_user: User = Depends(get_current_user),
):
    user_service = UserService(db)
    await user_service.delete_user(current_user.id)

    return {
        "status": "deleted",
        "user_id": current_user.id,
        "message": "User account deleted successfully"
    }

