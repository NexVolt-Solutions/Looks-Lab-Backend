from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, ConfigDict
from app.models.domain import QuestionType   # reuse enum
from app.schemas.subscription import SubscriptionStatus

AnswerType = Union[str, int, float, List[str], Dict[str, Any], None]


class DomainQuestionBase(BaseModel):
    domain: str
    question: str
    type: QuestionType
    options: Optional[List[str]] = None
    constraints: Optional[Dict[str, Any]] = None


class DomainQuestionOut(DomainQuestionBase):
    id: int
    seq: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class DomainAnswerBase(BaseModel):
    user_id: int
    question_id: int
    answer: Optional[AnswerType] = None


class DomainAnswerCreate(DomainAnswerBase):
    domain: str


class DomainAnswerOut(DomainAnswerBase):
    id: int
    domain: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class DomainProgressOut(BaseModel):
    user_id: int
    domain: str
    progress: Dict[str, Any]
    answered_questions: List[int]
    total_questions: int
    progress_percent: Optional[float] = None
    subscription_status: Optional[SubscriptionStatus] = None


class DomainFlowOut(BaseModel):
    status: str
    current: Optional[DomainQuestionOut] = None
    next: Optional[DomainQuestionOut] = None
    progress: DomainProgressOut
    redirect: Optional[str] = None

    # -------------------------------
    # AI Output Fields
    # -------------------------------
    ai_attributes: Optional[Dict[str, Any]] = None
    ai_health: Optional[Dict[str, Any]] = None
    ai_concerns: Optional[List[str]] = None
    ai_routine: Optional[Dict[str, Any]] = None
    ai_remedies: Optional[List[str]] = None
    ai_products: Optional[List[Dict[str, Any]]] = None
    ai_recovery: Optional[Dict[str, Any]] = None
    ai_progress: Optional[Dict[str, Any]] = None
    ai_message: Optional[str] = None
    ai_features: Optional[Dict[str, Any]] = None
    ai_exercises: Optional[List[Dict[str, Any]]] = None


class DomainSelectionResponse(BaseModel):
    """Response model for domain selection."""
    status: str
    domain: Optional[str] = None

