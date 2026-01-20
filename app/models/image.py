from datetime import datetime
from enum import Enum
from sqlalchemy import String, DateTime, ForeignKey, func, JSON, Index, text
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.core.database import Base


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

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    file_path: Mapped[str] = mapped_column(String(255), nullable=False)

    image_type: Mapped[ImageType | None] = mapped_column(String(20), nullable=True, index=True)

    status: Mapped[ImageStatus] = mapped_column(
        String(20),
        server_default=text("'pending'"),
        nullable=False,
        index=True
    )

    analysis_result: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    domain: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    view: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)


    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), onupdate=func.now())

    user: Mapped["User"] = relationship("User", back_populates="images")

