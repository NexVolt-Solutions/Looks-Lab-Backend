from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.domain import QuestionType
from app.schemas.subscription import SubscriptionStatus

AnswerType = str | int | float | list[str] | dict[str, Any] | None


class DomainQuestionOut(BaseModel):
    id: int
    domain: str
    step: Optional[str] = None
    question: str
    type: QuestionType
    options: Optional[list[str]] = None
    constraints: Optional[dict[str, Any]] = None
    seq: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DomainAnswerCreate(BaseModel):
    user_id: int = 0
    question_id: int
    answer: AnswerType = None
    domain: str


class DomainAnswerItem(BaseModel):
    question_id: int
    question: Optional[str] = None
    answer: AnswerType = None
    answered_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class DomainAnswersOut(BaseModel):
    user_id: int
    domain: str
    answers: list[DomainAnswerItem]


class DomainProgressOut(BaseModel):
    user_id: int
    domain: str
    progress: dict[str, Any]
    answered_questions: list[int]
    total_questions: int
    progress_percent: Optional[float] = None
    subscription_status: Optional[SubscriptionStatus] = None


class DomainFlowOut(BaseModel):
    status: str  # "ok" | "processing" | "completed"
    current: Optional[DomainQuestionOut] = None
    next: Optional[DomainQuestionOut] = None
    progress: DomainProgressOut
    redirect: Optional[str] = None
    ai_attributes: Optional[dict[str, Any]] = None
    ai_health: Optional[dict[str, Any]] = None
    ai_concerns: Optional[dict[str, Any]] = None
    ai_routine: Optional[dict[str, Any]] = None
    ai_remedies: Optional[dict[str, Any]] = None
    ai_products: Optional[list[dict[str, Any]]] = None
    ai_message: Optional[str] = None
    ai_exercises: Optional[dict[str, Any]] = None
    ai_progress: Optional[dict[str, Any]] = None
    ai_today_focus: Optional[list[dict[str, Any]]] = None
    ai_workout_summary: Optional[dict[str, Any]] = None
    ai_nutrition: Optional[dict[str, Any]] = None
    ai_recovery: Optional[dict[str, Any]] = None
    ai_features: Optional[dict[str, Any]] = None


class DomainProgressItem(BaseModel):
    domain: str
    icon_url: Optional[str] = None
    progress_percent: float = Field(..., ge=0, le=100)
    answered_questions: int = Field(..., ge=0)
    total_questions: int = Field(..., ge=0)
    is_completed: bool = Field(default=False)


class AllDomainsProgressOut(BaseModel):
    user_id: int
    domains: list[DomainProgressItem]
    overall_average: float = Field(..., ge=0, le=100)
    domains_started: int = Field(..., ge=0)
    domains_completed: int = Field(..., ge=0)
    total_domains: int = Field(..., ge=0)


class NutritionFacts(BaseModel):
    calories: float = Field(..., ge=0)
    protein: float = Field(..., ge=0)
    carbs: float = Field(..., ge=0)
    fat: float = Field(..., ge=0)
    fiber: float = Field(default=0, ge=0)
    sugar: float = Field(default=0, ge=0)


class FoodAnalysisOut(BaseModel):
    image_id: int
    image_url: str
    food_name: str
    portion_size: str
    confidence: int = Field(..., ge=0, le=100)
    nutrition: NutritionFacts
    ingredients: list[str] = Field(default=[])
    health_score: int = Field(..., ge=0, le=100)
    tip: Optional[str] = None


class BarcodeProductOut(BaseModel):
    barcode: str
    food_name: str
    brand: str = Field(default="")
    portion_size: str = Field(default="100g")
    nutrition: NutritionFacts
    image_url: Optional[str] = None
    tip: Optional[str] = None
    
    