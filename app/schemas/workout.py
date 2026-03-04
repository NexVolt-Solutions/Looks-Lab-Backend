from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum


class WorkoutFocus(str, Enum):
    flexibility = "flexibility"
    build_muscle = "build_muscle"
    fatloss = "fatloss"
    strength = "strength"


class GenerateWorkoutRequest(BaseModel):
    focus: WorkoutFocus
    intensity: str = Field(default="moderate")
    activity_level: str = Field(default="moderate")
    duration_minutes: int = Field(default=30, ge=10, le=120)


class WorkoutExercise(BaseModel):
    name: str
    duration_seconds: Optional[int] = None
    sets: Optional[int] = None
    reps: Optional[int] = None
    rest_seconds: int
    instructions: str
    benefits: str
    difficulty: str


class WorkoutInsight(BaseModel):
    title: str
    message: str


class WorkoutPlanOut(BaseModel):
    focus: str
    title: str
    description: str
    duration_minutes: int
    exercise_count: int
    intensity: str
    insight: WorkoutInsight
    exercises: list[WorkoutExercise]
    generated_at: datetime

