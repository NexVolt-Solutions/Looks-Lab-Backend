from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, DateTime, ForeignKey, func, Boolean, text, Index
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    __table_args__ = (
        Index("ix_refresh_token_lookup", "token"),
        Index("ix_refresh_token_user", "user_id"),
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
        unique=True
    )

    # ── Token Data ────────────────────────────────────────────
    token: Mapped[str] = mapped_column(
        String(2048),
        unique=True,
        nullable=False,
        index=True
    )

    # ── State ─────────────────────────────────────────────────
    is_revoked: Mapped[bool] = mapped_column(
        Boolean,
        server_default=text("false"),
        nullable=False
    )
    device_info: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    # ── Timestamps ────────────────────────────────────────────
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )
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
        back_populates="refresh_token"
    )

