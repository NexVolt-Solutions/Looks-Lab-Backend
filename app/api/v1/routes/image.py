from fastapi import APIRouter, Depends, Request, UploadFile, File, Query
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


class AnalysisResultPayload(BaseModel):
    analysis_result: dict | str


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
    await validate_upload_file(file)
    return await ImageService(db).upload_image(
        file=file,
        user_id=current_user.id,
        domain=domain,
        view=view,
        image_type=image_type
    )


@router.get("/", response_model=list[ImageOut])
async def get_my_images(
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
        image_status=image_status
    )


@router.get("/{image_id}", response_model=ImageOut)
async def get_image(
    image_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    return await ImageService(db).get_image(image_id, current_user.id)


@router.get("/{image_id}/url", response_model=ImageUrlOut)
async def get_image_url(
    image_id: int,
    expires_in: int = Query(3600, ge=60, le=86400),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    service = ImageService(db)
    image = await service.get_image(image_id, current_user.id)
    url = service.get_image_url(image, expires_in)
    return ImageUrlOut(image_id=image_id, url=url, expires_in=expires_in)


@router.patch("/{image_id}", response_model=ImageOut)
async def update_image(
    image_id: int,
    payload: ImageUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    return await ImageService(db).update_image(image_id, current_user.id, payload)


@router.delete("/{image_id}")
async def delete_image(
    image_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    await ImageService(db).delete_image(image_id, current_user.id)
    return {"status": "deleted", "image_id": image_id}

