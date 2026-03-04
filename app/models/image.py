from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, Integer, JSON, String, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

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

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    s3_key: Mapped[str | None] = mapped_column(String(512))
    url: Mapped[str | None] = mapped_column(String(1024))
    mime_type: Mapped[str | None] = mapped_column(String(100))
    file_size: Mapped[int | None] = mapped_column(Integer)

    image_type: Mapped[ImageType] = mapped_column(String(20), nullable=False, index=True)
    domain: Mapped[str | None] = mapped_column(String(50), index=True)
    view: Mapped[str | None] = mapped_column(String(50), index=True)

    status: Mapped[ImageStatus] = mapped_column(String(20), server_default=text("'pending'"), nullable=False, index=True)
    analysis_result: Mapped[dict | None] = mapped_column(JSON)
    error_message: Mapped[str | None] = mapped_column(String(512))

    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user: Mapped[User] = relationship("User", back_populates="images")

