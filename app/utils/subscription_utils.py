from fastapi import HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.models.subscription import Subscription
from app.schemas.subscription import SubscriptionCreate


def create_subscription_entry(payload: SubscriptionCreate, db: Session) -> Subscription:
    """Create a new subscription for a user."""
    new_sub = Subscription(
        user_id=payload.user_id,
        plan=payload.plan,
        status="active",
        payment_id=None,
        created_at=datetime.now(timezone.utc),
    )
    db.add(new_sub)
    db.commit()
    db.refresh(new_sub)
    return new_sub


def get_latest_subscription(user_id: int, db: Session) -> Subscription:
    """Fetch the most recent subscription for a user."""
    sub = (
        db.query(Subscription)
        .filter(Subscription.user_id == user_id)
        .order_by(Subscription.created_at.desc())
        .first()
    )
    if not sub:
        raise HTTPException(status_code=404, detail="No subscription found for this user")
    return sub


def cancel_subscription_entry(subscription_id: int, db: Session) -> Subscription:
    """Cancel an existing subscription."""
    sub = db.query(Subscription).filter(Subscription.id == subscription_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")

    sub.status = "cancelled"
    sub.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(sub)
    return sub

