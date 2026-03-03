from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    String, DateTime, ForeignKey, JSON,
    func, Boolean, text
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


# ============================================================
# ONBOARDING SESSION 
# ============================================================

class OnboardingSession(Base):
    
    __tablename__ = "onboarding_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="NULL = anonymous, set when user signs in"
    )

    selected_domain: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        index=True,
        comment="Domain selected by user (skincare, haircare, etc.)"
    )

    is_paid: Mapped[bool] = mapped_column(
        Boolean,
        server_default=text("false"),
        nullable=False,
        comment="Has user confirmed payment?"
    )

    is_completed: Mapped[bool] = mapped_column(
        Boolean,
        server_default=text("false"),
        nullable=False,
        comment="Has onboarding been completed?"
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

    # Relationships
    user: Mapped[User | None] = relationship(
        "User",
        back_populates="onboarding_sessions"
    )

    answers: Mapped[list["OnboardingAnswer"]] = relationship(
        "OnboardingAnswer",
        back_populates="session",
        cascade="all, delete-orphan"
    )


# ============================================================
# ONBOARDING QUESTIONS 
# ============================================================

class OnboardingQuestion(Base):
    """
    Onboarding questions seeded from JSON file.
    Frontend handles ordering and grouping.
    """
    __tablename__ = "onboarding_questions"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )

    step: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Step category (profile_setup, haircare, etc.)"
    )

    question: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="The question text"
    )

    type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Question type: text, number, choice, multi_choice"
    )

    options: Mapped[list[str] | None] = mapped_column(
        JSON,
        nullable=True,
        comment="Available options for choice/multi_choice questions"
    )

    constraints: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment="Validation constraints (e.g., min/max for numbers)"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Relationships
    answers: Mapped[list["OnboardingAnswer"]] = relationship(
        "OnboardingAnswer",
        back_populates="question",
        cascade="all, delete-orphan"
    )


# ============================================================
# ONBOARDING ANSWERS (linked to sessions)
# ============================================================

class OnboardingAnswer(Base):
    """
    User's answers to onboarding questions.
    
    Linked to SESSION (not user) because:
    - Anonymous users answer before signing in
    - Session gets linked to user after sign-in
    """
    __tablename__ = "onboarding_answers"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )

    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("onboarding_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Which session this answer belongs to"
    )

    question_id: Mapped[int] = mapped_column(
        ForeignKey("onboarding_questions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Which question was answered"
    )

    answer: Mapped[dict | list | str | int | float | None] = mapped_column(
        JSON,
        nullable=True,
        comment="The user's answer (can be string, number, list for multi_choice)"
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

    # Relationships
    session: Mapped["OnboardingSession"] = relationship(
        "OnboardingSession",
        back_populates="answers"
    )

    question: Mapped["OnboardingQuestion"] = relationship(
        "OnboardingQuestion",
        back_populates="answers"
    )
    
    