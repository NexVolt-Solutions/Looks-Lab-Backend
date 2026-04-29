from fastapi import APIRouter, Depends, Request, UploadFile, File, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.core.file_validation import validate_upload_file
from app.core.rate_limit import RateLimits, limiter
from app.models.image import ImageStatus, ImageType
from app.models.user import User
from app.schemas.image import ImageOut, ImageUpdate, SimpleImageOut
from app.services.image_service import ImageService
from app.utils.jwt_utils import get_current_user

router = APIRouter()


class AnalysisResultPayload(BaseModel):
    analysis_result: dict | str


@router.post("/upload/simple", response_model=SimpleImageOut)
@limiter.limit(RateLimits.UPLOAD)
async def upload_simple_image(
    request: Request,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    """
    Simple image upload with no domain or view metadata.
    Use this for profile photos, onboarding screens, or any
    general purpose image upload not tied to a specific domain.
    """
    detected_mime_type = await validate_upload_file(file)
    return await ImageService(db).upload_image(
        file=file,
        user_id=current_user.id,
        domain=None,
        view=None,
        image_type=ImageType.uploaded,
        detected_mime_type=detected_mime_type,
    )


@router.post("/upload", response_model=ImageOut)
@limiter.limit(RateLimits.UPLOAD)
async def upload_domain_image(
    request: Request,
    file: UploadFile = File(...),
    domain: str | None = None,
    view: str | None = None,
    image_type: ImageType = ImageType.uploaded,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    """
    Domain image upload with optional domain and view metadata.
    Use this when uploading images for AI analysis (skincare, haircare, facial, etc).
    - domain: the domain this image belongs to e.g. skincare, haircare
    - view: the angle/type of photo e.g. front, side, hair_top
    """
    detected_mime_type = await validate_upload_file(file)
    return await ImageService(db).upload_image(
        file=file,
        user_id=current_user.id,
        domain=domain,
        view=view,
        image_type=image_type,
        detected_mime_type=detected_mime_type,
    )


@router.get("/album", response_model=list[ImageOut])
@limiter.limit(RateLimits.DEFAULT)
async def get_my_album(
    request: Request,
    domain: str | None = Query(None),
    view: str | None = Query(None),
    image_status: ImageStatus | None = Query(None, alias="status"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    return await ImageService(db).get_user_images(
        user_id=current_user.id,
        domain=domain,
        view=view,
        image_status=image_status,
    )


@router.get("/{image_id}", response_model=ImageOut)
@limiter.limit(RateLimits.DEFAULT)
async def get_image(
    request: Request,
    image_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    return await ImageService(db).get_image(image_id, current_user.id)


@router.patch("/{image_id}", response_model=ImageOut)
@limiter.limit(RateLimits.DEFAULT)
async def update_image(
    request: Request,
    image_id: int,
    payload: ImageUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    return await ImageService(db).update_image(image_id, current_user.id, payload)


@router.delete("/{image_id}")
@limiter.limit(RateLimits.DEFAULT)
async def delete_image(
    request: Request,
    image_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    await ImageService(db).delete_image(image_id, current_user.id)
    return {"status": "deleted", "image_id": image_id}
