"""
Image schemas.
Pydantic models for image upload and management.
"""
from pydantic import BaseModel
from datetime import datetime
from typing import Any

from app.models.image import ImageStatus, ImageType


class ImageBase(BaseModel):
    file_path: str
    image_type: ImageType | None = None
    status: ImageStatus = ImageStatus.pending
    analysis_result: str | dict[str, Any] | None = None
    domain: str | None = None
    view: str | None = None


class ImageCreate(ImageBase):
    user_id: int


class ImageUpdate(BaseModel):
    analysis_result: str | dict[str, Any] | None = None
    status: ImageStatus | None = None
    image_type: ImageType | None = None
    domain: str | None = None
    view: str | None = None


class ImageOut(BaseModel):
    id: int
    user_id: int
    file_path: str
    image_type: ImageType | None = None
    status: ImageStatus
    analysis_result: str | dict[str, Any] | None = None
    domain: str | None = None
    view: str | None = None
    uploaded_at: datetime
    processed_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}

