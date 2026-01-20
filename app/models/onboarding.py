from datetime import datetime
from sqlalchemy import (
    String, DateTime, ForeignKey, JSON, UniqueConstraint, func, Integer, Boolean, Index, text
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
import uuid

from app.core.database import Base


class OnboardingSession(Base):
    __tablename__ = "onboarding_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    selected_domain: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)

    is_paid: Mapped[bool] = mapped_column(Boolean, server_default=text("false"), nullable=False)
    payment_confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), onupdate=func.now())

    answers: Mapped[list["OnboardingAnswer"]] = relationship(
        "OnboardingAnswer", back_populates="session", cascade="all, delete-orphan"
    )
    user: Mapped["User"] = relationship("User", back_populates="onboarding_sessions")


class OnboardingQuestion(Base):
    __tablename__ = "onboarding_questions"
    __table_args__ = (
        UniqueConstraint("step", "question", name="uq_onboarding_step_question"),
        UniqueConstraint("step", "seq", name="uq_onboarding_step_seq"),
        Index("ix_step_seq", "step", "seq"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    step: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    question: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    options: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    constraints: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    seq: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), onupdate=func.now())

    answers: Mapped[list["OnboardingAnswer"]] = relationship(
        "OnboardingAnswer", back_populates="question", cascade="all, delete-orphan"
    )


class OnboardingAnswer(Base):
    __tablename__ = "onboarding_answers"
    __table_args__ = (
        Index("ix_session_question", "session_id", "question_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("onboarding_sessions.id", ondelete="CASCADE"),
        nullable=False
    )
    question_id: Mapped[int] = mapped_column(
        ForeignKey("onboarding_questions.id", ondelete="CASCADE"),
        nullable=False
    )

    answer: Mapped[dict | list | str | int | None] = mapped_column(JSON, nullable=True)

    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), onupdate=func.now())

    question: Mapped["OnboardingQuestion"] = relationship("OnboardingQuestion", back_populates="answers")
    session: Mapped["OnboardingSession"] = relationship("OnboardingSession", back_populates="answers")

