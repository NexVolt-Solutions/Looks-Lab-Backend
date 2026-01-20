from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.insight import Insight
from app.schemas.insight import InsightCreate

VALID_CATEGORIES = {"health", "facial", "diet", "fashion", "workout", "skincare", "hair care"}


def validate_category(category: str):
    if category not in VALID_CATEGORIES:
        raise HTTPException(status_code=422, detail="Invalid category")


def create_insight_entry(payload: InsightCreate, db: Session) -> Insight:
    validate_category(payload.category)
    new_insight = Insight(
        user_id=payload.user_id,
        category=payload.category,
        content=payload.content,
        source=payload.source,
        created_at=datetime.now(timezone.utc),
    )
    db.add(new_insight)
    db.commit()
    db.refresh(new_insight)
    return new_insight


def get_insight_or_404(insight_id: int, db: Session) -> Insight:
    insight = db.query(Insight).filter(Insight.id == insight_id).first()
    if not insight:
        raise HTTPException(status_code=404, detail="Insight not found")
    return insight


def get_user_insights(user_id: int, db: Session):
    return db.query(Insight).filter(Insight.user_id == user_id).all()


def update_insight_record(insight_id: int, content, source, db: Session) -> Insight:
    insight = get_insight_or_404(insight_id, db)
    if content is not None:
        insight.content = content
    if source is not None:
        insight.source = source
    insight.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(insight)
    return insight


def delete_insight_record(insight_id: int, db: Session):
    insight = get_insight_or_404(insight_id, db)
    db.delete(insight)
    db.commit()
    return {"status": "deleted", "insight_id": insight_id}

