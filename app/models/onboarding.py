from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, JSON, String, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class OnboardingSession(Base):
    __tablename__ = "onboarding_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    selected_domain: Mapped[str | None] = mapped_column(String(50), index=True)

    is_paid: Mapped[bool] = mapped_column(Boolean, server_default=text("false"), nullable=False)
    is_completed: Mapped[bool] = mapped_column(Boolean, server_default=text("false"), nullable=False)

    payment_confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user: Mapped[User | None] = relationship("User", back_populates="onboarding_sessions")
    answers: Mapped[list[OnboardingAnswer]] = relationship("OnboardingAnswer", back_populates="session", cascade="all, delete-orphan")


class OnboardingQuestion(Base):
    __tablename__ = "onboarding_questions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    step: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    question: Mapped[str] = mapped_column(String(500), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    options: Mapped[list[str] | None] = mapped_column(JSON)
    constraints: Mapped[dict | None] = mapped_column(JSON)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    answers: Mapped[list[OnboardingAnswer]] = relationship("OnboardingAnswer", back_populates="question", cascade="all, delete-orphan")


class OnboardingAnswer(Base):
    __tablename__ = "onboarding_answers"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("onboarding_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("onboarding_questions.id", ondelete="CASCADE"), nullable=False, index=True)

    answer: Mapped[dict | list | str | int | float | None] = mapped_column(JSON)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    session: Mapped[OnboardingSession] = relationship("OnboardingSession", back_populates="answers")
    question: Mapped[OnboardingQuestion] = relationship("OnboardingQuestion", back_populates="answers")

