"""Diet domain schemas for meal plan generation."""
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class DietFocus(str, Enum):
    """Diet focus areas."""
    BUILD_MUSCLE = "build_muscle"
    MAINTENANCE = "maintenance"
    CLEAN_ENERGETIC = "clean_energetic"
    FATLOSS = "fatloss"


class ActivityLevel(str, Enum):
    """Activity level for calorie calculation."""
    SEDENTARY = "sedentary"
    LIGHT = "light"
    MODERATE = "moderate"
    ACTIVE = "active"
    VERY_ACTIVE = "very_active"


class GenerateMealPlanRequest(BaseModel):
    """Request to generate meal plan."""
    focus: DietFocus
    calorie_target: int | None = Field(default=None, ge=1200, le=4000)
    meal_count: int = Field(default=3, ge=2, le=6)
    snack_count: int = Field(default=2, ge=0, le=4)
    dietary_preferences: list[str] | None = None
    allergies: list[str] | None = None
    cuisine_preference: str | None = None


class Macros(BaseModel):
    """Macronutrient breakdown."""
    protein: int
    carbs: int
    fats: int


class Meal(BaseModel):
    """Individual meal in the plan."""
    type: str  # breakfast, lunch, dinner
    name: str
    prep_time_minutes: int
    calories: int
    macros: Macros
    ingredients: list[str]
    instructions: list[str]
    benefits: str


class Snack(BaseModel):
    """Snack item."""
    name: str
    prep_time_minutes: int
    calories: int
    macros: Macros
    ingredients: list[str]
    instructions: list[str]


class CalorieInfo(BaseModel):
    """Calorie information."""
    intake: int
    activity: str


class DietInsight(BaseModel):
    """Nutritional insight."""
    title: str
    message: str


class DailyTotals(BaseModel):
    """Daily nutritional totals."""
    calories: int
    protein: int
    carbs: int
    fats: int


class MealPlanOut(BaseModel):
    """Generated meal plan response."""
    focus: str
    title: str
    description: str
    calories: CalorieInfo
    insight: DietInsight
    meal_count: int
    snack_count: int
    total_prep_time_minutes: int
    meals: list[Meal]
    snacks: list[Snack]
    daily_totals: DailyTotals
    generated_at: datetime

