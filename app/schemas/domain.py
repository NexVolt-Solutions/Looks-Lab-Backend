"""
Domain schemas.
Pydantic models for domain questionnaire flows and AI processing.
"""
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import Any

from app.models.domain import QuestionType
from app.schemas.subscription import SubscriptionStatus

AnswerType = str | int | float | list[str] | dict[str, Any] | None


class DomainQuestionBase(BaseModel):
    domain: str
    question: str
    type: QuestionType
    options: list[str] | None = None
    constraints: dict[str, Any] | None = None


class DomainQuestionOut(DomainQuestionBase):
    id: int
    seq: int | None = None
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class DomainAnswerBase(BaseModel):
    user_id: int
    question_id: int
    answer: AnswerType = None


class DomainAnswerCreate(DomainAnswerBase):
    domain: str


class DomainAnswerOut(DomainAnswerBase):
    id: int
    domain: str
    created_at: datetime
    completed_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class DomainProgressOut(BaseModel):
    user_id: int
    domain: str
    progress: dict[str, Any]
    answered_questions: list[int]
    total_questions: int
    progress_percent: float | None = None
    subscription_status: SubscriptionStatus | None = None


class DomainFlowOut(BaseModel):
    status: str
    current: DomainQuestionOut | None = None
    next: DomainQuestionOut | None = None
    progress: DomainProgressOut
    redirect: str | None = None

    ai_attributes: dict[str, Any] | None = None
    ai_health: dict[str, Any] | None = None
    ai_concerns: list[str] | None = None
    ai_routine: dict[str, Any] | None = None
    ai_remedies: list[str] | None = None
    ai_products: list[dict[str, Any]] | None = None
    ai_recovery: dict[str, Any] | None = None
    ai_progress: dict[str, Any] | None = None
    ai_message: str | None = None
    ai_features: dict[str, Any] | None = None
    ai_exercises: list[dict[str, Any]] | None = None


class DomainSelectionResponse(BaseModel):
    status: str
    domain: str | None = None

