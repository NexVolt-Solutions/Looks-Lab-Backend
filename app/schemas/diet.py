from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum


class DietFocus(str, Enum):
    build_muscle = "build_muscle"
    maintenance = "maintenance"
    clean_energetic = "clean_energetic"
    fatloss = "fatloss"


class GenerateMealPlanRequest(BaseModel):
    focus: DietFocus
    calorie_target: Optional[int] = Field(default=None, ge=1200, le=4000)
    meal_count: int = Field(default=3, ge=2, le=6)
    snack_count: int = Field(default=2, ge=0, le=4)
    dietary_preferences: Optional[list[str]] = None
    allergies: Optional[list[str]] = None
    cuisine_preference: Optional[str] = None


class Macros(BaseModel):
    protein: int
    carbs: int
    fats: int


class Meal(BaseModel):
    type: str
    name: str
    prep_time_minutes: int
    calories: int
    macros: Macros
    ingredients: list[str]
    instructions: list[str]
    benefits: str


class Snack(BaseModel):
    name: str
    prep_time_minutes: int
    calories: int
    macros: Macros
    ingredients: list[str]
    instructions: list[str]


class CalorieInfo(BaseModel):
    intake: int
    activity: str


class DietInsight(BaseModel):
    title: str
    message: str


class DailyTotals(BaseModel):
    calories: int
    protein: int
    carbs: int
    fats: int


class MealPlanOut(BaseModel):
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

