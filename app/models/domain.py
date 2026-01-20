from datetime import datetime
from enum import Enum
from sqlalchemy import (
    String, DateTime, ForeignKey, JSON, UniqueConstraint, func, Integer, Index
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.core.database import Base


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
    question: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[QuestionType] = mapped_column(String(20), nullable=False)
    options: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    constraints: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    seq: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), onupdate=func.now())

    answers: Mapped[list["DomainAnswer"]] = relationship(
        "DomainAnswer", back_populates="question", cascade="all, delete-orphan"
    )


class DomainAnswer(Base):
    __tablename__ = "domain_answers"
    __table_args__ = (
        Index("ix_user_domain", "user_id", "domain"),
        Index("ix_question_user", "question_id", "user_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    question_id: Mapped[int] = mapped_column(
        ForeignKey("domain_questions.id", ondelete="CASCADE"),
        nullable=False
    )

    domain: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    answer: Mapped[str | int | list | dict | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), onupdate=func.now())

    question: Mapped["DomainQuestion"] = relationship("DomainQuestion", back_populates="answers")
    user: Mapped["User"] = relationship("User", back_populates="domain_answers")

