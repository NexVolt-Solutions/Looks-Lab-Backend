from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Union, Dict, Any
from app.models.image import ImageStatus, ImageType


class ImageBase(BaseModel):
    file_path: str
    image_type: Optional[ImageType] = None
    status: ImageStatus = ImageStatus.pending
    analysis_result: Optional[Union[str, Dict[str, Any]]] = None

    # NEW fields
    domain: Optional[str] = None
    view: Optional[str] = None


class ImageCreate(ImageBase):
    user_id: int


class ImageUpdate(BaseModel):
    analysis_result: Optional[Union[str, Dict[str, Any]]] = None
    status: Optional[ImageStatus] = None
    image_type: Optional[ImageType] = None

    # Allow updating domain/view if needed
    domain: Optional[str] = None
    view: Optional[str] = None


class ImageOut(BaseModel):
    id: int
    user_id: int
    file_path: str
    image_type: Optional[ImageType] = None
    status: ImageStatus
    analysis_result: Optional[Union[str, Dict[str, Any]]] = None

    # NEW fields
    domain: Optional[str] = None
    view: Optional[str] = None

    uploaded_at: datetime
    processed_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

