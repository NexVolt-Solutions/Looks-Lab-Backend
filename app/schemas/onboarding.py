"""
Onboarding schemas.
Pydantic models for onboarding session flow and question progression.
"""
from datetime import datetime
from uuid import UUID
from typing import Any

from pydantic import BaseModel, field_validator, model_validator, ConfigDict, Field

from app.schemas.subscription import SubscriptionStatus

AnswerType = str | int | float | list[str] | dict[str, Any] | None


class OnboardingQuestionOut(BaseModel):
    id: int
    step: str
    question: str
    type: str
    options: list[str] | None = None
    constraints: dict[str, int | float | str] | None = None

    model_config = ConfigDict(from_attributes=True)


class OnboardingAnswerCreate(BaseModel):
    question_id: int
    answer: AnswerType
    question_type: str | None = None
    question_options: list[str] | None = None
    constraints: dict[str, int | float | str] | None = None

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
        constraints = self.constraints or {}

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
    completed_at: datetime | None = None
    updated_at: datetime | None = None
    question_type: str | None = None
    step: str | None = None

    model_config = ConfigDict(from_attributes=True)


class OnboardingProgressOut(BaseModel):
    session_id: UUID
    step: str
    answered_questions: list[int]
    total_questions: int
    progress: dict[str, Any]  # ✅ Fixed: allows nested dicts from calculate_progress()


class DomainSelectionOut(BaseModel):
    session_id: UUID
    selected_domain: str
    subscription_status: SubscriptionStatus
    is_paid: bool
    payment_confirmed_at: datetime | None = None


class OnboardingFlowOut(BaseModel):
    status: str
    current: OnboardingQuestionOut | None = None
    next: OnboardingQuestionOut | None = None
    progress: OnboardingProgressOut
    redirect: str | None = None


class OnboardingSessionOut(BaseModel):
    id: UUID
    user_id: int | None = None
    created_at: datetime
    updated_at: datetime | None = None
    selected_domain: str | None = None
    is_paid: bool
    payment_confirmed_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class OnboardingAnswerWithQuestion(BaseModel):
    """
    Onboarding answer with its question context.
    Used by GET /onboarding/users/me/answers endpoint.
    """
    question_id: int
    question: str = Field(..., description="The question text")
    step: str = Field(..., description="Which onboarding step this belongs to")
    answer: AnswerType
    answered_at: datetime | None = None


class OnboardingAnswersResponse(BaseModel):
    """
    Full response for GET /onboarding/users/me/answers.
    Returns all answers with question context.
    """
    user_id: int
    answers: list[OnboardingAnswerWithQuestion]


class WellnessMetricsOut(BaseModel):
    """
    Wellness metrics extracted from onboarding answers.
    Used for Home screen wellness overview section.

    Displayed on Home screen as:
    - Your Height: 5.2 ft
    - Your Weight: 76 kg
    - Sleep Hours: 6-7 hours
    - Water Intake: 1.5-2.5 liters
    """
    height: AnswerType = Field(
        default=None,
        description="User's height from profile_setup step"
    )
    weight: AnswerType = Field(
        default=None,
        description="User's weight from profile_setup step"
    )
    sleep_hours: AnswerType = Field(
        default=None,
        description="Daily sleep hours from daily_lifestyle step"
    )
    water_intake: AnswerType = Field(
        default=None,
        description="Daily water intake from daily_lifestyle step"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "height": "5.2 ft",
                "weight": "76 kg",
                "sleep_hours": "6-7 hours",
                "water_intake": "1.5 - 2.5 liters"
            }
        }
    )

