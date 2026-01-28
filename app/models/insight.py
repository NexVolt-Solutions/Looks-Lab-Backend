"""
Insight model.
"""
from datetime import datetime
from enum import Enum
from sqlalchemy import String, DateTime, ForeignKey, func, JSON, Index
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.core.database import Base


class InsightCategory(str, Enum):
    skincare = "skincare"
    hair_care = "hair care"
    fashion = "fashion"
    workout = "workout"
    quit_porn = "quit porn"
    diet = "diet"
    height = "height"
    facial = "facial"


class Insight(Base):
    __tablename__ = "insights"
    __table_args__ = (
        Index("ix_insight_user_category", "user_id", "category"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    category: Mapped[InsightCategory] = mapped_column(String(50), nullable=False, index=True)
    content: Mapped[dict | str] = mapped_column(JSON, nullable=False)
    source: Mapped[str | None] = mapped_column(String(50), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), onupdate=func.now())

    user: Mapped["User"] = relationship("User", back_populates="insights")

