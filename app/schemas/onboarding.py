from datetime import datetime
from typing import Optional, List, Dict, Union, Any
from uuid import UUID
from pydantic import BaseModel, field_validator, model_validator, ConfigDict
from app.schemas.subscription import SubscriptionStatus


AnswerType = Union[str, int, float, List[str], Dict[str, Any], None]


class OnboardingQuestionOut(BaseModel):
    id: int
    step: str
    question: str
    type: str
    options: Optional[List[str]] = None
    constraints: Optional[Dict[str, Union[int, float, str]]] = None

    model_config = ConfigDict(from_attributes=True)


class OnboardingAnswerCreate(BaseModel):
    question_id: int
    answer: AnswerType

    question_type: Optional[str] = None
    question_options: Optional[List[str]] = None
    question_constraints: Optional[Dict[str, Union[int, float, str]]] = None

    @field_validator("answer", mode="before")
    def validate_not_empty(cls, v):
        if v is None or (isinstance(v, str) and not str(v).strip()):
            raise ValueError("Answer cannot be empty")
        return v

    @model_validator(mode="after")
    def validate_against_question(self) -> "OnboardingAnswerCreate":
        q_type = (self.question_type or "").strip().lower()
        answer = self.answer
        options = self.question_options or []
        constraints = self.question_constraints or {}

        if q_type in ["number", "numeric"]:
            if not isinstance(answer, (int, float)):
                raise ValueError("Answer must be a number")
            min_val = constraints.get("min")
            max_val = constraints.get("max")
            if min_val is not None and answer < min_val:
                raise ValueError(f"Value must be >= {min_val}")
            if max_val is not None and answer > max_val:
                raise ValueError(f"Value must be <= {max_val}")

        elif q_type in ["choice", "single-choice"]:
            if answer not in options:
                raise ValueError(f"Answer must be one of {options}")

        elif q_type in ["multi-choice"]:
            if not isinstance(answer, list):
                raise ValueError("Answer must be a list")
            invalid = [a for a in answer if a not in options]
            if invalid:
                raise ValueError(f"Invalid options: {invalid}. Must be from {options}")

        elif q_type == "text":
            if not isinstance(answer, str):
                raise ValueError("Answer must be text")

        return self


class OnboardingAnswerOut(BaseModel):
    id: int
    session_id: UUID
    question_id: int
    answer: AnswerType
    completed_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    question_type: Optional[str] = None
    step: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class OnboardingProgressOut(BaseModel):
    session_id: UUID
    step: str
    answered_questions: List[int]
    total_questions: int
    progress: Dict[str, Union[int, bool]]


class DomainSelectionOut(BaseModel):
    session_id: UUID
    selected_domain: str
    subscription_status: SubscriptionStatus
    is_paid: bool
    payment_confirmed_at: Optional[datetime] = None


class OnboardingFlowOut(BaseModel):
    status: str
    current: Optional[OnboardingQuestionOut] = None
    next: Optional[OnboardingQuestionOut] = None
    progress: OnboardingProgressOut
    redirect: Optional[str] = None


class OnboardingSessionOut(BaseModel):
    id: UUID
    user_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    selected_domain: Optional[str] = None
    is_paid: bool
    payment_confirmed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

