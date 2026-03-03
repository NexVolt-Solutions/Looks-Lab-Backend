from datetime import datetime
from uuid import UUID
from typing import Any, Union, List, Optional

from pydantic import BaseModel, field_validator, ConfigDict, Field

AnswerType = Union[str, int, float, List[str], dict[str, Any], None]


# ===========================================================
# QUESTION OUTPUT
# ===========================================================

class OnboardingQuestionOut(BaseModel):
    id: int
    step: str
    question: str
    type: str
    options: Optional[List[str]] = None
    constraints: Optional[dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


# ===========================================================
# ANSWER CREATE
# ===========================================================

class OnboardingAnswerCreate(BaseModel):
    question_id: int
    answer: AnswerType = Field(...)

    @field_validator("answer")
    @classmethod
    def validate_answer(cls, v):

        if v is None:
            raise ValueError("Answer cannot be empty")

        if isinstance(v, str) and not v.strip():
            raise ValueError("Answer cannot be empty string")

        return v

    model_config = ConfigDict(from_attributes=True)


# ===========================================================
# ANSWER CONTEXT OUTPUT
# ===========================================================

class OnboardingAnswerWithQuestion(BaseModel):
    question_id: int
    question: str
    step: str
    answer: AnswerType
    answered_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ===========================================================
# ANSWERS RESPONSE
# ===========================================================

class OnboardingAnswersResponse(BaseModel):
    user_id: int
    answers: List[OnboardingAnswerWithQuestion]

    model_config = ConfigDict(from_attributes=True)


# ===========================================================
# PROGRESS RESPONSE
# ===========================================================

class OnboardingProgressOut(BaseModel):
    session_id: UUID
    step: str
    answered_questions: List[int] = Field(default_factory=list)
    total_questions: int
    progress: float = Field(ge=0, le=100)


# ===========================================================
# FLOW RESPONSE
# ===========================================================

class OnboardingFlowOut(BaseModel):
    status: str
    current: Optional[OnboardingQuestionOut] = None
    next: Optional[OnboardingQuestionOut] = None
    progress: OnboardingProgressOut
    redirect: Optional[str] = None


# ===========================================================
# SESSION OUTPUT
# ===========================================================

class OnboardingSessionOut(BaseModel):
    id: UUID
    user_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    selected_domain: Optional[str] = None
    is_paid: bool = False
    payment_confirmed_at: Optional[datetime] = None
    is_completed: bool = False

    model_config = ConfigDict(from_attributes=True)


# ===========================================================
# WELLNESS METRICS OUTPUT
# ===========================================================

class WellnessMetricsOut(BaseModel):
    height: Optional[AnswerType] = None
    weight: Optional[AnswerType] = None
    sleep_hours: Optional[AnswerType] = None
    water_intake: Optional[AnswerType] = None
    daily_quote: str = Field(min_length=1)

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "height": "5.2 ft",
                "weight": "76 kg",
                "sleep_hours": "6-7 hours",
                "water_intake": "1.5 - 2.5 liters",
                "daily_quote": "Keep pushing forward."
            }
        }
    )
    
    