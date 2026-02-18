from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import String, DateTime, ForeignKey, func, JSON, Index, text, Integer
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class ImageStatus(str, Enum):
    pending = "pending"
    processed = "processed"
    failed = "failed"


class ImageType(str, Enum):
    uploaded = "uploaded"
    generated = "generated"
    preview = "preview"
    final = "final"


class Image(Base):
    __tablename__ = "images"
    __table_args__ = (
        Index("ix_user_status", "user_id", "status"),
        Index("ix_user_type", "user_id", "image_type"),
        Index("ix_user_domain_view", "user_id", "domain", "view"),
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

    # ── File Storage ──────────────────────────────────────────
    file_path: Mapped[str] = mapped_column(
        String(512),
        nullable=False
    )
    s3_key: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True
    )
    url: Mapped[str | None] = mapped_column(
        String(1024),
        nullable=True
    )
    mime_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )
    file_size: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True
    )

    # ── Image Metadata ────────────────────────────────────────
    image_type: Mapped[ImageType] = mapped_column(
        String(20),
        nullable=False,
        index=True
    )
    domain: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        index=True
    )
    view: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        index=True
    )

    # ── Processing State ──────────────────────────────────────
    status: Mapped[ImageStatus] = mapped_column(
        String(20),
        server_default=text("'pending'"),
        nullable=False,
        index=True
    )
    analysis_result: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True               # Populated after AI processing
    )
    error_message: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True
    )

    # ── Timestamps ────────────────────────────────────────────
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
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
        back_populates="images"
    )

