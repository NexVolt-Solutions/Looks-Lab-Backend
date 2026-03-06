from __future__ import annotations
from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, JSON, String, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.enums import DomainEnum
if TYPE_CHECKING:
    from app.models.user import User


class Insight(Base):
    __tablename__ = "insights"
    __table_args__ = (
        Index("ix_insight_user_category", "user_id", "category"),
        Index("ix_insight_user_read", "user_id", "is_read"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    category: Mapped[DomainEnum] = mapped_column(String(50), nullable=False, index=True)
    content: Mapped[dict | str] = mapped_column(JSON, nullable=False)
    source: Mapped[str | None] = mapped_column(String(50))
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, server_default=text("false"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user: Mapped[User] = relationship("User", back_populates="insights")
    
    