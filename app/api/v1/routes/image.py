"""
Image routes.
Handles image upload, retrieval, and management.
"""
from fastapi import APIRouter, Depends, Request, UploadFile, File, Query
from fastapi import status as http_status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.core.file_validation import validate_upload_file
from app.core.rate_limit import RateLimits, limiter
from app.models.image import ImageStatus, ImageType
from app.models.user import User
from app.schemas.image import ImageOut, ImageUpdate, ImageUrlOut
from app.services.image_service import ImageService
from app.utils.jwt_utils import get_current_user

router = APIRouter()


# ── Request Bodies ────────────────────────────────────────────────

class AnalysisResultPayload(BaseModel):
    """Proper body for mark_processed endpoint."""
    analysis_result: dict | str


# ── Upload ────────────────────────────────────────────────────────

@router.post("/", response_model=ImageOut)
@limiter.limit(RateLimits.UPLOAD)
async def upload_image(
    request: Request,
    file: UploadFile = File(...),
    domain: str | None = None,
    view: str | None = None,
    image_type: ImageType = ImageType.uploaded,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    """
    Upload an image for any domain.

    Query params:
        domain: skincare | haircare | facial | fashion | diet | height | workout | quit porn
        view: front | back | left | right | meal | barcode
        image_type: uploaded | generated | preview | final
    """
    await validate_upload_file(file)

    image_service = ImageService(db)
    return await image_service.upload_image(
        file=file,
        user_id=current_user.id,
        domain=domain,
        view=view,
        image_type=image_type
    )


# ── Retrieval ─────────────────────────────────────────────────────


@router.get("/", response_model=list[ImageOut])
async def get_my_images(
    request: Request,  # noqa: ARG001
    domain: str | None = Query(None),
    view: str | None = Query(None),
    image_status: ImageStatus | None = Query(None, alias="status"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    """Get all images for current user, optionally filtered by domain/view/status."""
    image_service = ImageService(db)
    return await image_service.get_user_images(
        user_id=current_user.id,
        domain=domain,
        view=view,
        image_status=image_status
    )


@router.get("/{image_id}", response_model=ImageOut)
async def get_image(
    request: Request,  # noqa: ARG001
    image_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific image by ID."""
    image_service = ImageService(db)
    return await image_service.get_image(image_id, current_user.id)


@router.get("/{image_id}/url", response_model=ImageUrlOut)
async def get_image_url(
    request: Request,  # noqa: ARG001
    image_id: int,
    expires_in: int = Query(3600, ge=60, le=86400),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    """Get pre-signed URL for an image. Expires in 60s–24h."""
    image_service = ImageService(db)
    image = await image_service.get_image(image_id, current_user.id)
    url = image_service.get_image_url(image, expires_in)

    return ImageUrlOut(
        image_id=image_id,
        url=url,
        expires_in=expires_in
    )


# ── Update ────────────────────────────────────────────────────────

@router.patch("/{image_id}", response_model=ImageOut)
async def update_image(
    request: Request,  # noqa: ARG001
    image_id: int,
    payload: ImageUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    """Update image metadata."""
    image_service = ImageService(db)
    return await image_service.update_image(image_id, current_user.id, payload)


@router.patch("/{image_id}/processed", response_model=ImageOut)
async def mark_image_processed(
    request: Request,  # noqa: ARG001
    image_id: int,
    payload: AnalysisResultPayload,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    """Mark image as processed with AI analysis result."""
    image_service = ImageService(db)
    await image_service.get_image(image_id, current_user.id)
    return await image_service.mark_processed(image_id, payload.analysis_result)


@router.patch("/{image_id}/failed", response_model=ImageOut)
async def mark_image_failed(
    request: Request,  # noqa: ARG001
    image_id: int,
    error_message: str | None = None,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    """Mark image as failed with optional error message."""
    image_service = ImageService(db)
    await image_service.get_image(image_id, current_user.id)
    return await image_service.mark_failed(image_id, error_message)


# ── Delete ────────────────────────────────────────────────────────

@router.delete("/{image_id}")
async def delete_image(
    request: Request,  # noqa: ARG001
    image_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    """Delete an image from storage and database."""
    image_service = ImageService(db)
    await image_service.delete_image(image_id, current_user.id)

    return {
        "status": "deleted",
        "image_id": image_id,
        "message": "Image deleted successfully"
    }

