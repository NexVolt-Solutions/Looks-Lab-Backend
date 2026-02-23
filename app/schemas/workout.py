"""Workout domain schemas for AI-powered workout plan generation."""
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class WorkoutFocus(str, Enum):
    """Workout focus areas."""
    FLEXIBILITY = "flexibility"
    BUILD_MUSCLE = "build_muscle"
    FATLOSS = "fatloss"
    STRENGTH = "strength"


class GenerateWorkoutRequest(BaseModel):
    """Request to generate workout plan."""
    focus: WorkoutFocus
    intensity: str = Field(default="moderate", description="Workout intensity: low, moderate, high")
    activity_level: str = Field(default="moderate", description="User's activity level")
    duration_minutes: int = Field(default=30, ge=10, le=120, description="Target workout duration in minutes")


class WorkoutExercise(BaseModel):
    """Single exercise in workout plan."""
    name: str
    duration_seconds: int | None = None
    sets: int | None = None
    reps: int | None = None
    rest_seconds: int
    instructions: str
    benefits: str
    difficulty: str  # beginner, intermediate, advanced


class WorkoutInsight(BaseModel):
    """Motivational insight for workout."""
    title: str
    message: str


class WorkoutPlanOut(BaseModel):
    """Generated workout plan response."""
    focus: str
    title: str
    description: str
    duration_minutes: int
    exercise_count: int
    intensity: str
    insight: WorkoutInsight
    exercises: list[WorkoutExercise]
    generated_at: datetime

