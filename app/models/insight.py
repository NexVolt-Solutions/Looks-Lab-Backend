from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import String, DateTime, ForeignKey, func, JSON, Index, Boolean, text
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class InsightCategory(str, Enum):
    """
    Fixed: values match DomainEnum exactly
    so InsightCategory can be mapped from domain name directly
    """
    skincare = "skincare"
    haircare = "haircare"
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
        Index("ix_insight_user_read", "user_id", "is_read"),
    )

    # ── Primary Key ───────────────────────────────────────────
    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    # ── Foreign Key ───────────────────────────────────────────
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # ── Insight Data ──────────────────────────────────────────
    category: Mapped[InsightCategory] = mapped_column(
        String(50),
        nullable=False,
        index=True
    )
    content: Mapped[dict | str] = mapped_column(
        JSON,
        nullable=False
    )
    source: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )

    # ── State ─────────────────────────────────────────────────
    is_read: Mapped[bool] = mapped_column(
        Boolean,
        server_default=text("false"),
        nullable=False
    )

    # ── Timestamps ────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # ── Relationships ─────────────────────────────────────────
    user: Mapped[User] = relationship(
        "User",
        back_populates="insights"
    )

