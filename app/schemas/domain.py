"""
Domain schemas.
Pydantic models for domain questionnaire flows and AI processing.
"""
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.domain import QuestionType
from app.schemas.subscription import SubscriptionStatus

AnswerType = str | int | float | list[str] | dict[str, Any] | None


# ── Question Schemas ──────────────────────────────────────────────

class DomainQuestionBase(BaseModel):
    domain: str
    question: str
    type: QuestionType
    options: list[str] | None = None
    constraints: dict[str, Any] | None = None


class DomainQuestionOut(DomainQuestionBase):
    id: int
    seq: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ── Answer Schemas ────────────────────────────────────────────────

class DomainAnswerBase(BaseModel):
    user_id: int = 0
    question_id: int
    answer: AnswerType = None


class DomainAnswerCreate(DomainAnswerBase):
    domain: str


class DomainAnswerOut(DomainAnswerBase):
    id: int
    domain: str
    created_at: datetime
    completed_at: datetime | None = None
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DomainAnswerItem(BaseModel):
    """Single answer item with question context."""
    question_id: int
    question: str | None = None
    answer: AnswerType = None
    answered_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class DomainAnswersOut(BaseModel):
    """
     Added: Response for GET /{domain}/answers
    Returns all user answers for a domain with question context.
    """
    user_id: int
    domain: str
    answers: list[DomainAnswerItem]

    model_config = {
        "json_schema_extra": {
            "example": {
                "user_id": 42,
                "domain": "skincare",
                "answers": [
                    {
                        "question_id": 1,
                        "question": "What is your skin type?",
                        "answer": "Oily",
                        "answered_at": "2026-02-17T10:00:00Z"
                    }
                ]
            }
        }
    }


# ── Progress Schemas ──────────────────────────────────────────────

class DomainProgressOut(BaseModel):
    user_id: int
    domain: str
    progress: dict[str, Any]
    answered_questions: list[int]
    total_questions: int
    progress_percent: float | None = None
    subscription_status: SubscriptionStatus | None = None


class DomainSelectionResponse(BaseModel):
    status: str
    domain: str | None = None


# ── Flow Schema ───────────────────────────────────────────────────

class DomainFlowOut(BaseModel):
    status: str
    current: DomainQuestionOut | None = None
    next: DomainQuestionOut | None = None
    progress: DomainProgressOut
    redirect: str | None = None

    # ── Skincare / Haircare / Facial ──────────────────────────
    ai_attributes: dict[str, Any] | None = None
    ai_health: dict[str, Any] | None = None
    ai_concerns: dict[str, Any] | None = None

    # ── All domains ───────────────────────────────────────────
    ai_routine: dict[str, Any] | None = None
    ai_remedies: dict[str, Any] | None = None
    ai_products: list[dict[str, Any]] | None = None
    ai_message: str | None = None

    # ── Height / Workout / Facial ─────────────────────────────
    ai_exercises: dict[str, Any] | None = None
    ai_progress: dict[str, Any] | None = None
    ai_today_focus: list[dict[str, Any]] | None = None

    # ── Workout specific ──────────────────────────────────────
    ai_workout_summary: dict[str, Any] | None = None

    # ── Diet specific ─────────────────────────────────────────
    ai_nutrition: dict[str, Any] | None = None

    # ── Quit Porn specific ────────────────────────────────────
    ai_recovery: dict[str, Any] | None = None

    # ── Facial specific ───────────────────────────────────────
    ai_features: dict[str, Any] | None = None


# ── Progress Overview Schemas ─────────────────────────────────────

class DomainProgressItem(BaseModel):
    """Single domain progress item for overview chart."""
    domain: str = Field(..., description="Domain name")
    progress_percent: float = Field(..., ge=0, le=100)
    answered_questions: int = Field(..., ge=0)
    total_questions: int = Field(..., ge=0)
    is_completed: bool = Field(default=False)

    model_config = {
        "json_schema_extra": {
            "example": {
                "domain": "skincare",
                "progress_percent": 75.0,
                "answered_questions": 8,
                "total_questions": 10,
                "is_completed": False
            }
        }
    }


class AllDomainsProgressOut(BaseModel):
    """Progress overview across all domains for Home screen chart."""
    user_id: int
    domains: list[DomainProgressItem]
    overall_average: float = Field(..., ge=0, le=100)
    domains_started: int = Field(..., ge=0)
    domains_completed: int = Field(..., ge=0)
    total_domains: int = Field(..., ge=0)

    model_config = {
        "json_schema_extra": {
            "example": {
                "user_id": 123,
                "domains": [
                    {
                        "domain": "skincare",
                        "progress_percent": 75.0,
                        "answered_questions": 8,
                        "total_questions": 10,
                        "is_completed": False
                    }
                ],
                "overall_average": 58.3,
                "domains_started": 2,
                "domains_completed": 1,
                "total_domains": 8
            }
        }
    }


# ── Diet Food Schemas ─────────────────────────────────────────────

class NutritionFacts(BaseModel):
    """Nutrition facts for a food item."""
    calories: float = Field(..., ge=0, description="Calories in kcal")
    protein: float = Field(..., ge=0, description="Protein in grams")
    carbs: float = Field(..., ge=0, description="Carbohydrates in grams")
    fat: float = Field(..., ge=0, description="Fat in grams")
    fiber: float = Field(default=0, ge=0, description="Fiber in grams")
    sugar: float = Field(default=0, ge=0, description="Sugar in grams")


class FoodAnalysisOut(BaseModel):
    """Response for POST /domains/diet/foods/analyze"""
    image_id: int
    image_url: str
    food_name: str = Field(..., description="Detected food name")
    portion_size: str = Field(..., description="Estimated portion size")
    confidence: int = Field(..., ge=0, le=100, description="AI confidence %")
    nutrition: NutritionFacts
    ingredients: list[str] = Field(default=[], description="Detected ingredients")
    health_score: int = Field(..., ge=0, le=100, description="Health score 0-100")
    tip: str | None = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "image_id": 42,
                "image_url": "https://cdn.example.com/food.jpg",
                "food_name": "Fresh Salad Bowl",
                "portion_size": "1 bowl (300g)",
                "confidence": 85,
                "nutrition": {
                    "calories": 280,
                    "protein": 8,
                    "carbs": 32,
                    "fat": 12,
                    "fiber": 4,
                    "sugar": 6
                },
                "ingredients": ["lettuce", "tomato", "cucumber"],
                "health_score": 88,
                "tip": "Include balanced portions for better nutrition tracking."
            }
        }
    }


class BarcodeProductOut(BaseModel):
    """Response for GET /domains/diet/foods/barcode/{barcode}"""
    barcode: str
    food_name: str
    brand: str = Field(default="")
    portion_size: str = Field(default="100g")
    nutrition: NutritionFacts
    image_url: str | None = None
    tip: str | None = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "barcode": "3017620422003",
                "food_name": "Nutella",
                "brand": "Ferrero",
                "portion_size": "100g",
                "nutrition": {
                    "calories": 539,
                    "protein": 6.3,
                    "carbs": 57.5,
                    "fat": 30.9,
                    "fiber": 3.4,
                    "sugar": 56.3
                },
                "image_url": "https://images.openfoodfacts.org/...",
                "tip": "Nutrition values are per 100g."
            }
        }
    }

