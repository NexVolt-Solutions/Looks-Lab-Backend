from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class DomainScorePoint(BaseModel):
    """A single score data point for a domain at a specific time."""
    domain: str
    score: float
    recorded_at: datetime

    model_config = {"from_attributes": True}


class DomainProgressSeries(BaseModel):
    """All score points for a single domain over the requested period."""
    domain: str
    icon_url: Optional[str] = None
    scores: list[DomainScorePoint]
    first_score: Optional[float] = None   
    latest_score: Optional[float] = None  
    change: Optional[float] = None       


class ProgressGraphOut(BaseModel):
    """Response for GET /users/me/progress/graph"""
    period: str 
    domains: list[DomainProgressSeries]
    overall_first: float = 0.0   
    overall_latest: float = 0.0  
    overall_change: float = 0.0
    
    