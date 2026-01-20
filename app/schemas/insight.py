from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Union, Dict, Any
from app.models.insight import InsightCategory


class InsightBase(BaseModel):
    category: InsightCategory
    content: Union[str, Dict[str, Any]]
    source: Optional[str] = None


class InsightCreate(InsightBase):
    user_id: int


class InsightUpdate(BaseModel):
    category: Optional[InsightCategory] = None
    content: Optional[Union[str, Dict[str, Any]]] = None
    source: Optional[str] = None


class InsightOut(InsightBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

