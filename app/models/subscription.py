from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import String, DateTime, ForeignKey, func, text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


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
    __table_args__ = (
        Index("ix_subscription_user", "user_id"),
        Index("ix_subscription_status", "status"),
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

    # ── Plan Details ──────────────────────────────────────────
    plan: Mapped[PlanType] = mapped_column(
        String(20),
        nullable=False
    )
    status: Mapped[SubscriptionStatus] = mapped_column(
        String(20),
        server_default=text("'pending'"),
        nullable=False,
        index=True
    )

    # ── Stripe Integration ────────────────────────────────────
    payment_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )
    stripe_customer_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True
    )
    stripe_subscription_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True
    )

    # ── Lifecycle Timestamps ──────────────────────────────────
    start_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    end_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    trial_end: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    cancelled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # ── Audit Timestamps ──────────────────────────────────────
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
        back_populates="subscription"
    )

