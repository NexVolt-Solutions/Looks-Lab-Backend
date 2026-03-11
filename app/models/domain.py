from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, Integer, JSON, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class QuestionType(str, Enum):
    text = "text"
    choice = "choice"
    multi_choice = "multi-choice"
    numeric = "numeric"


class DomainQuestion(Base):
    __tablename__ = "domain_questions"
    __table_args__ = (
        UniqueConstraint("domain", "question", name="uq_domain_question"),
        UniqueConstraint("domain", "seq", name="uq_domain_seq"),
        Index("ix_domain_seq", "domain", "seq"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    domain: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    step: Mapped[str | None] = mapped_column(String(50), nullable=True)
    question: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[QuestionType] = mapped_column(String(20), nullable=False)
    options: Mapped[list[str] | None] = mapped_column(JSON)
    constraints: Mapped[dict | None] = mapped_column(JSON)
    seq: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    answers: Mapped[list[DomainAnswer]] = relationship("DomainAnswer", back_populates="question", cascade="all, delete-orphan")


class DomainAnswer(Base):
    __tablename__ = "domain_answers"
    __table_args__ = (
        UniqueConstraint("user_id", "question_id", name="uq_user_question_answer"),
        Index("ix_user_domain", "user_id", "domain"),
        Index("ix_question_user", "question_id", "user_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("domain_questions.id", ondelete="CASCADE"), nullable=False)

    domain: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    answer: Mapped[str | int | list | dict | None] = mapped_column(JSON)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    question: Mapped[DomainQuestion] = relationship("DomainQuestion", back_populates="answers")
    user: Mapped[User] = relationship("User", back_populates="domain_answers")
    
    