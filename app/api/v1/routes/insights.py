from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.schemas.insight import InsightCreate, InsightUpdate, InsightOut
from app.utils.jwt_utils import get_current_user
from app.utils.insight_utils import (
    create_insight_entry,
    get_insight_or_404,
    get_user_insights,
    update_insight_record,
    delete_insight_record,
)

router = APIRouter()


@router.post("/", response_model=InsightOut)
def create_insight(
    payload: InsightCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new insight for the authenticated user."""
    # Force the insight to belong to the logged-in user
    payload.user_id = current_user.id
    return create_insight_entry(payload, db)


@router.get("/{insight_id}", response_model=InsightOut)
def get_insight(
    insight_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Fetch a single insight by ID, only if it belongs to the authenticated user."""
    insight = get_insight_or_404(insight_id, db)
    if insight.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this insight")
    return insight


@router.get("/me", response_model=list[InsightOut])
def get_my_insights(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Fetch all insights belonging to the authenticated user."""
    return get_user_insights(current_user.id, db)


@router.patch("/{insight_id}", response_model=InsightOut)
def update_insight(
    insight_id: int,
    payload: InsightUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update content or source of an insight if it belongs to the authenticated user."""
    insight = get_insight_or_404(insight_id, db)
    if insight.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this insight")
    return update_insight_record(insight_id, payload.content, payload.source, db)


@router.delete("/{insight_id}")
def delete_insight(
    insight_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete an insight record if it belongs to the authenticated user."""
    insight = get_insight_or_404(insight_id, db)
    if insight.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this insight")
    return delete_insight_record(insight_id, db)

