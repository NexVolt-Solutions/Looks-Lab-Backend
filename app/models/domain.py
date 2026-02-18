from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import (
    String, DateTime, ForeignKey, JSON,
    UniqueConstraint, func, Integer, Index
)
from sqlalchemy.orm import relationship, Mapped, mapped_column

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

    # ── Primary Key ───────────────────────────────────────────
    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    # ── Question Data ─────────────────────────────────────────
    domain: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True
    )
    question: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    type: Mapped[QuestionType] = mapped_column(
        String(20),
        nullable=False
    )
    options: Mapped[list[str] | None] = mapped_column(
        JSON,
        nullable=True
    )
    constraints: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True
    )
    seq: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True
    )

    # ── Timestamps ────────────────────────────────────────────
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
    answers: Mapped[list[DomainAnswer]] = relationship(
        "DomainAnswer",
        back_populates="question",
        cascade="all, delete-orphan"
    )


class DomainAnswer(Base):
    __tablename__ = "domain_answers"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "question_id",
            name="uq_user_question_answer"
        ),
        Index("ix_user_domain", "user_id", "domain"),
        Index("ix_question_user", "question_id", "user_id"),
    )

    # ── Primary Key ───────────────────────────────────────────
    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    # ── Foreign Keys ──────────────────────────────────────────
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    question_id: Mapped[int] = mapped_column(
        ForeignKey("domain_questions.id", ondelete="CASCADE"),
        nullable=False
    )

    # ── Answer Data ───────────────────────────────────────────
    domain: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True
    )
    answer: Mapped[str | int | list | dict | None] = mapped_column(
        JSON,
        nullable=True
    )

    # ── Timestamps ────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # ── Relationships ─────────────────────────────────────────
    question: Mapped[DomainQuestion] = relationship(
        "DomainQuestion",
        back_populates="answers"
    )
    user: Mapped[User] = relationship(
        "User",
        back_populates="domain_answers"
    )

