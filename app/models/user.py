from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, DateTime, Boolean, Integer, func, text
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.onboarding import OnboardingSession
    from app.models.domain import DomainAnswer
    from app.models.image import Image
    from app.models.insight import Insight
    from app.models.subscription import Subscription
    from app.models.refresh_token import RefreshToken


class User(Base):
    __tablename__ = "users"

    # ── Primary Key ───────────────────────────────────────────
    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    # ── Identity ──────────────────────────────────────────────
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False
    )
    name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )
    provider: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        index=True
    )

    # ── Auth State ────────────────────────────────────────────
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        server_default=text("true"),
        nullable=False
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        server_default=text("true"),
        nullable=False
    )

    # ── Google Provider ───────────────────────────────────────
    google_sub: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True
    )
    google_picture: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True
    )
    last_google_id_token: Mapped[str | None] = mapped_column(
        String(2048),
        nullable=True
    )

    # ── Apple Provider ────────────────────────────────────────
    apple_sub: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True
    )
    last_apple_id_token: Mapped[str | None] = mapped_column(
        String(2048),
        nullable=True
    )

    # ── Profile ───────────────────────────────────────────────
    age: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True
    )
    gender: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True
    )
    profile_image: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True
    )

    # ── Preferences ───────────────────────────────────────────
    notifications_enabled: Mapped[bool] = mapped_column(
        Boolean,
        server_default=text("true"),
        nullable=False
    )

    # ── Onboarding State ──────────────────────────────────────
    onboarding_complete: Mapped[bool] = mapped_column(
        Boolean,
        server_default=text("false"),
        nullable=False
    )

    # ── Timestamps ────────────────────────────────────────────
    last_login: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
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
    onboarding_sessions: Mapped[list[OnboardingSession]] = relationship(
        "OnboardingSession",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    domain_answers: Mapped[list[DomainAnswer]] = relationship(
        "DomainAnswer",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    images: Mapped[list[Image]] = relationship(
        "Image",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    insights: Mapped[list[Insight]] = relationship(
        "Insight",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    subscription: Mapped[Subscription | None] = relationship(
        "Subscription",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )
    refresh_token: Mapped[RefreshToken | None] = relationship(
        "RefreshToken",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )

    