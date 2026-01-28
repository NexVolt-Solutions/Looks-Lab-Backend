"""
Insight schemas.
Pydantic models for AI-generated insights.
"""
from pydantic import BaseModel
from datetime import datetime
from typing import Any

from app.models.insight import InsightCategory


class InsightBase(BaseModel):
    category: InsightCategory
    content: str | dict[str, Any]
    source: str | None = None


class InsightCreate(InsightBase):
    user_id: int


class InsightUpdate(BaseModel):
    category: InsightCategory | None = None
    content: str | dict[str, Any] | None = None
    source: str | None = None


class InsightOut(InsightBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}

