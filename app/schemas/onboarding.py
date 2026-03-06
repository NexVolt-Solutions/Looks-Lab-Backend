from datetime import datetime
from uuid import UUID
from typing import Any, Union, List, Optional

from pydantic import BaseModel, field_validator, ConfigDict, Field

AnswerType = Union[str, int, float, List[str], dict[str, Any], None]


class OnboardingQuestionOut(BaseModel):
    id: int
    step: str
    question: str
    type: str
    options: Optional[List[str]] = None
    constraints: Optional[dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


class OnboardingAnswerCreate(BaseModel):
    question_id: int
    answer: AnswerType = Field(...)

    @field_validator("answer")
    @classmethod
    def validate_answer(cls, v):
        if v is None or (isinstance(v, str) and not v.strip()):
            raise ValueError("Answer cannot be empty")
        return v


class OnboardingAnswerWithQuestion(BaseModel):
    question_id: int
    question: str
    step: str
    answer: AnswerType
    answered_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class OnboardingAnswersResponse(BaseModel):
    user_id: int
    answers: List[OnboardingAnswerWithQuestion]


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


class WellnessItem(BaseModel):
    value: Optional[AnswerType] = None
    icon_url: str


class WellnessMetricsOut(BaseModel):
    height: WellnessItem
    weight: WellnessItem
    sleep_hours: WellnessItem
    water_intake: WellnessItem
    daily_quote: str = Field(min_length=1)
    
    