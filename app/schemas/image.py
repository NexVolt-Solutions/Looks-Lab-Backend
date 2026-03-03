from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field
from app.models.image import ImageStatus, ImageType


class ImageCreate(BaseModel):
    user_id: int
    file_path: Optional[str] = None
    s3_key: Optional[str] = None
    url: Optional[str] = None
    mime_type: Optional[str] = None
    file_size: Optional[int] = None
    image_type: Optional[ImageType] = None
    status: ImageStatus = ImageStatus.pending
    analysis_result: Optional[str | dict[str, Any]] = None
    domain: Optional[str] = None
    view: Optional[str] = None


class ImageUpdate(BaseModel):
    analysis_result: Optional[str | dict[str, Any]] = None
    status: Optional[ImageStatus] = None
    image_type: Optional[ImageType] = None
    domain: Optional[str] = None
    view: Optional[str] = None


class ImageOut(BaseModel):
    id: int
    user_id: int
    file_path: Optional[str] = None
    s3_key: Optional[str] = None
    url: Optional[str] = None
    mime_type: Optional[str] = None
    file_size: Optional[int] = None
    image_type: ImageType
    status: ImageStatus
    domain: Optional[str] = None
    view: Optional[str] = None
    analysis_result: Optional[str | dict[str, Any]] = None
    error_message: Optional[str] = None
    uploaded_at: datetime
    processed_at: Optional[datetime] = None
    updated_at: datetime

    model_config = {"from_attributes": True}


class ImageUrlOut(BaseModel):
    image_id: int
    url: str
    expires_in: int = Field(..., ge=60, le=86400)

