from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel
from app.models.insight import InsightCategory


class InsightCreate(BaseModel):
    category: InsightCategory
    content: str | dict[str, Any]
    source: Optional[str] = None
    user_id: int = 0
    is_read: bool = False


class InsightUpdate(BaseModel):
    category: Optional[InsightCategory] = None
    content: Optional[str | dict[str, Any]] = None
    source: Optional[str] = None
    is_read: Optional[bool] = None


class InsightOut(BaseModel):
    id: int
    user_id: int
    category: InsightCategory
    content: str | dict[str, Any]
    source: Optional[str] = None
    is_read: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class InsightListOut(BaseModel):
    insights: list[InsightOut]
    total: int
    unread_count: int

