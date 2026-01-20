from fastapi import HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.models.user import User
from app.schemas.user import UserUpdate


def get_user_or_404(user_id: int, db: Session) -> User:
    """Fetch a user or raise 404 if not found."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def update_user_fields(user: User, payload: UserUpdate, db: Session) -> User:
    """Apply updates from payload to user model."""
    if payload.name is not None:
        user.name = payload.name
    if payload.age is not None:
        user.age = payload.age
    if payload.gender is not None:
        user.gender = payload.gender
    if payload.profile_image is not None:
        user.profile_image = payload.profile_image
    if payload.notifications_enabled is not None:
        user.notifications_enabled = payload.notifications_enabled

    user.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)
    return user


def delete_user(user: User, db: Session) -> None:
    """Delete a user from DB."""
    db.delete(user)
    db.commit()

