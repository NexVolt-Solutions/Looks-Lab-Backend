from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field
from app.enums import DomainEnum


class InsightCreate(BaseModel):
    category: DomainEnum
    content: str | dict[str, Any]
    source: Optional[str] = None
    user_id: int = 0
    score: Optional[float] = Field(default=None, ge=0, le=100)
    is_read: bool = False


class InsightUpdate(BaseModel):
    content: Optional[str | dict[str, Any]] = None
    source: Optional[str] = None
    category: Optional[DomainEnum] = None
    score: Optional[float] = Field(default=None, ge=0, le=100)
    is_read: Optional[bool] = None


class InsightOut(BaseModel):
    id: int
    user_id: int
    category: DomainEnum
    content: str | dict[str, Any]
    source: Optional[str] = None
    score: Optional[float] = None
    is_read: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class InsightListOut(BaseModel):
    insights: list[InsightOut]
    total: int
    unread_count: int
    
    