from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.schemas.user import UserOut, UserUpdate
from app.utils.jwt_utils import get_current_user
from app.utils.user_utils import get_user_or_404, update_user_fields, delete_user

router = APIRouter(tags=["Users"])


# --------------------------- # GET Authenticated User Profile # ---------------------------
@router.get("/me", response_model=UserOut)
def get_my_user(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Fetch the authenticated user's profile."""
    return get_user_or_404(current_user.id, db)


# --------------------------- # PATCH Update Authenticated User # ---------------------------
@router.patch("/me", response_model=UserOut)
def update_my_user(
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update the authenticated user's profile fields, including notifications toggle."""
    user = get_user_or_404(current_user.id, db)
    return update_user_fields(user, payload, db)


# --------------------------- # DELETE Authenticated User # ---------------------------
@router.delete("/me")
def delete_my_user(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete the authenticated user's account."""
    user = get_user_or_404(current_user.id, db)
    delete_user(user, db)
    return {"status": "deleted", "user_id": current_user.id}

