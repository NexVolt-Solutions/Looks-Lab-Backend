from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Integer, String, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.domain import DomainAnswer
    from app.models.image import Image
    from app.models.insight import Insight
    from app.models.onboarding import OnboardingSession
    from app.models.refresh_token import RefreshToken
    from app.models.subscription import Subscription


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    name: Mapped[str | None] = mapped_column(String(100))
    provider: Mapped[str | None] = mapped_column(String(20), index=True)

    is_active: Mapped[bool] = mapped_column(Boolean, server_default=text("true"), nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, server_default=text("true"), nullable=False)

    google_sub: Mapped[str | None] = mapped_column(String(255), index=True)
    google_picture: Mapped[str | None] = mapped_column(String(512))
    last_google_id_token: Mapped[str | None] = mapped_column(String(2048))

    apple_sub: Mapped[str | None] = mapped_column(String(255), index=True)
    last_apple_id_token: Mapped[str | None] = mapped_column(String(2048))

    age: Mapped[int | None] = mapped_column(Integer)
    gender: Mapped[str | None] = mapped_column(String(20))
    profile_image: Mapped[str | None] = mapped_column(String(512))

    notifications_enabled: Mapped[bool] = mapped_column(Boolean, server_default=text("true"), nullable=False)
    onboarding_complete: Mapped[bool] = mapped_column(Boolean, server_default=text("false"), nullable=False)

    last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    onboarding_sessions: Mapped[list[OnboardingSession]] = relationship("OnboardingSession", back_populates="user", cascade="all, delete-orphan")
    domain_answers: Mapped[list[DomainAnswer]] = relationship("DomainAnswer", back_populates="user", cascade="all, delete-orphan")
    images: Mapped[list[Image]] = relationship("Image", back_populates="user", cascade="all, delete-orphan")
    insights: Mapped[list[Insight]] = relationship("Insight", back_populates="user", cascade="all, delete-orphan")
    subscription: Mapped[Subscription | None] = relationship("Subscription", back_populates="user", uselist=False, cascade="all, delete-orphan")
    refresh_tokens: Mapped[list[RefreshToken]] = relationship("RefreshToken", back_populates="user", uselist=True, cascade="all, delete-orphan")

    