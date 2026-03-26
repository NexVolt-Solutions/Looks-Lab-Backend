from datetime import date
from typing import Optional
from pydantic import BaseModel, Field


class WorkoutCompletionSave(BaseModel):
    date: date
    completed_indices: list[int] = Field(default=[])
    total_exercises: int = Field(default=6)


class WorkoutCompletionOut(BaseModel):
    date: date
    completed_indices: list[int]
    total_exercises: int
    score: float


class WorkoutSummaryItem(BaseModel):
    date: date
    score: float
    completed: int
    total: int


# Keep old name for backward compatibility
WeeklyWorkoutSummaryItem = WorkoutSummaryItem


class WorkoutProgressSummaryOut(BaseModel):
    user_id: int
    period: str                        # "week" | "month" | "year"
    average_score: float               # average score for the period
    total_days_active: int             # days with at least 1 exercise completed
    total_days_in_period: int          # total days in the period
    consistency_percent: float         # total_days_active / total_days_in_period * 100
    days: list[WorkoutSummaryItem]     # daily breakdown


# Keep old schema for backward compatibility
class WeeklyWorkoutSummaryOut(BaseModel):
    user_id: int
    week_average: float
    days: list[WorkoutSummaryItem]


class DailyRecoverySave(BaseModel):
    date: date
    sleep: bool = False
    water: bool = False
    stretched: bool = False
    rested: bool = False


class DailyRecoveryOut(BaseModel):
    date: date
    sleep: bool
    water: bool
    stretched: bool
    rested: bool


class WorkoutStatsOut(BaseModel):
    weekly_calories: int        # estimated calories burned this week
    consistency_percent: float  # % of days active this week
    strength_label: str         # e.g. "+12%" from AI intensity
    
    