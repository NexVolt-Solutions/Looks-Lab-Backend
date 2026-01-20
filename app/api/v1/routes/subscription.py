from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.schemas.subscription import SubscriptionCreate, SubscriptionOut
from app.utils.jwt_utils import get_current_user
from app.utils.subscription_utils import (
    create_subscription_entry,
    get_latest_subscription,
    cancel_subscription_entry,
)

router = APIRouter(tags=["Subscriptions"])


# --------------------------- # POST Create Subscription # ---------------------------
@router.post("/", response_model=SubscriptionOut)
def create_subscription(
    payload: SubscriptionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new subscription for the authenticated user."""
    payload.user_id = current_user.id  # force ownership
    return create_subscription_entry(payload, db)


# --------------------------- # GET Authenticated User Subscription # ---------------------------
@router.get("/me", response_model=SubscriptionOut)
def get_my_subscription(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Fetch the most recent subscription for the authenticated user."""
    return get_latest_subscription(current_user.id, db)


# --------------------------- # PATCH Cancel Subscription # ---------------------------
@router.patch("/{subscription_id}/cancel", response_model=SubscriptionOut)
def cancel_subscription(
    subscription_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Cancel an existing subscription if it belongs to the authenticated user."""
    subscription = get_latest_subscription(current_user.id, db)
    if not subscription or subscription.id != subscription_id:
        raise HTTPException(status_code=403, detail="Not authorized to cancel this subscription")
    return cancel_subscription_entry(subscription_id, db)

