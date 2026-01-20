from datetime import datetime
from enum import Enum
from sqlalchemy import String, DateTime, ForeignKey, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class PlanType(str, Enum):
    weekly = "weekly"
    monthly = "monthly"
    yearly = "yearly"


class SubscriptionStatus(str, Enum):
    pending = "pending"
    active = "active"
    expired = "expired"
    cancelled = "cancelled"


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True
    )

    # Plan details
    plan: Mapped[PlanType] = mapped_column(String(20), nullable=False)
    status: Mapped[SubscriptionStatus] = mapped_column(
        String(20),
        server_default=text("'pending'"),
        nullable=False,
        index=True
    )

    # Lifecycle timestamps
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    end_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Audit timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), onupdate=func.now())

    # Optional payment reference (external provider ID)
    payment_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Relationship back to User
    user: Mapped["User"] = relationship("User", back_populates="subscription")

