"""
Insight schemas.
Pydantic models for AI-generated insights.
"""
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models.insight import InsightCategory


# ── Base ──────────────────────────────────────────────────────────

class InsightBase(BaseModel):
    category: InsightCategory
    content: str | dict[str, Any]
    source: str | None = None


# ── Create ────────────────────────────────────────────────────────

class InsightCreate(InsightBase):
    user_id: int = 0
    is_read: bool = False


# ── Update ────────────────────────────────────────────────────────

class InsightUpdate(BaseModel):
    category: InsightCategory | None = None
    content: str | dict[str, Any] | None = None
    source: str | None = None
    is_read: bool | None = None


# ── Output ────────────────────────────────────────────────────────

class InsightOut(InsightBase):
    id: int
    user_id: int
    is_read: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class InsightListOut(BaseModel):
    """
     Added: Response for GET /me with summary stats.
    Useful for showing unread badge count in UI.
    """
    insights: list[InsightOut]
    total: int
    unread_count: int

    model_config = {
        "json_schema_extra": {
            "example": {
                "insights": [
                    {
                        "id": 1,
                        "user_id": 42,
                        "category": "skincare",
                        "content": "Your skin needs more hydration.",
                        "source": "ai_analysis",
                        "is_read": False,
                        "created_at": "2026-02-17T10:00:00Z",
                        "updated_at": "2026-02-17T10:00:00Z"
                    }
                ],
                "total": 5,
                "unread_count": 2
            }
        }
    }

