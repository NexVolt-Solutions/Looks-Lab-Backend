"""
User schemas.
Pydantic models for user profile management.
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

from app.schemas.base import UserBase
from app.schemas.subscription import SubscriptionOut


class UserCreate(BaseModel):
    email: str
    name: str | None = None
    notifications_enabled: bool = True


class UserUpdate(BaseModel):
    name: str | None = None
    age: int | None = None
    gender: str | None = None
    profile_image: str | None = None
    notifications_enabled: bool | None = None


class UserOut(UserBase):
    name: str | None = None
    age: int | None = None
    gender: str | None = None
    profile_image: str | None = None
    notifications_enabled: bool
    created_at: datetime
    updated_at: datetime | None = None
    subscription: SubscriptionOut | None = None

    model_config = {"from_attributes": True}


# ==================== NEW: WEEKLY PROGRESS SCHEMAS ====================

class DailyScore(BaseModel):
    """Single day's progress score for the weekly chart."""
    day: str = Field(..., description="Day label e.g. Mon, Tue")
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    score: float = Field(..., ge=0, le=100, description="Progress score 0-100")

    model_config = {
        "json_schema_extra": {
            "example": {
                "day": "Mon",
                "date": "2026-02-10",
                "score": 45.5
            }
        }
    }


class WeeklyProgressOut(BaseModel):
    """
    Weekly progress data for Home screen chart.
    Shows Mon-Sun progress scores calculated from
    domain question completion.
    """
    user_id: int
    labels: list[str] = Field(
        ...,
        description="Day labels for chart X-axis e.g. ['Mon','Tue',...,'Sun']"
    )
    scores: list[float] = Field(
        ...,
        description="Progress scores for chart Y-axis (0-100)"
    )
    days: list[DailyScore] = Field(
        ...,
        description="Detailed daily breakdown"
    )
    week_average: float = Field(
        ...,
        ge=0,
        le=100,
        description="Average score for the week"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "user_id": 123,
                "labels": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
                "scores": [0, 30, 45, 60, 55, 70, 75],
                "days": [
                    {"day": "Mon", "date": "2026-02-10", "score": 0},
                    {"day": "Tue", "date": "2026-02-11", "score": 30},
                    {"day": "Wed", "date": "2026-02-12", "score": 45},
                    {"day": "Thu", "date": "2026-02-13", "score": 60},
                    {"day": "Fri", "date": "2026-02-14", "score": 55},
                    {"day": "Sat", "date": "2026-02-15", "score": 70},
                    {"day": "Sun", "date": "2026-02-16", "score": 75}
                ],
                "week_average": 47.9
            }
        }
    }

