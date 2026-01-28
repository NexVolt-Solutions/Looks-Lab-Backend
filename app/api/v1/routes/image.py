"""
Image routes.
Handles image upload, retrieval, and management.
"""
from fastapi import APIRouter, Depends, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.models.user import User
from app.models.image import ImageStatus, ImageType
from app.schemas.image import ImageOut, ImageUpdate
from app.services.image_service import ImageService
from app.utils.jwt_utils import get_current_user

router = APIRouter()


@router.post("/", response_model=ImageOut)
async def upload_image(
        file: UploadFile = File(...),
        domain: str | None = None,
        view: str | None = None,
        image_type: ImageType = ImageType.uploaded,
        db: AsyncSession = Depends(get_async_db),
        current_user: User = Depends(get_current_user),
):
    image_service = ImageService(db)

    return await image_service.upload_image(
        file=file,
        user_id=current_user.id,
        domain=domain,
        view=view,
        image_type=image_type
    )


@router.post("/diet/scan-food", response_model=ImageOut)
async def scan_food(
        file: UploadFile = File(...),
        db: AsyncSession = Depends(get_async_db),
        current_user: User = Depends(get_current_user),
):
    image_service = ImageService(db)

    return await image_service.upload_image(
        file=file,
        user_id=current_user.id,
        domain="diet",
        view="meal",
        image_type=ImageType.uploaded
    )


@router.post("/diet/scan-barcode", response_model=ImageOut)
async def scan_barcode(
        file: UploadFile = File(...),
        db: AsyncSession = Depends(get_async_db),
        current_user: User = Depends(get_current_user),
):
    image_service = ImageService(db)

    return await image_service.upload_image(
        file=file,
        user_id=current_user.id,
        domain="diet",
        view="barcode",
        image_type=ImageType.uploaded
    )


@router.post("/diet/gallery", response_model=ImageOut)
async def upload_diet_gallery(
        file: UploadFile = File(...),
        db: AsyncSession = Depends(get_async_db),
        current_user: User = Depends(get_current_user),
):
    image_service = ImageService(db)

    return await image_service.upload_image(
        file=file,
        user_id=current_user.id,
        domain="diet",
        view="gallery",
        image_type=ImageType.uploaded
    )


@router.get("/{image_id}", response_model=ImageOut)
async def get_image(
        image_id: int,
        db: AsyncSession = Depends(get_async_db),
        current_user: User = Depends(get_current_user),
):
    image_service = ImageService(db)
    return await image_service.get_image(image_id, current_user.id)


@router.get("/", response_model=list[ImageOut])
async def get_my_images(
        domain: str | None = Query(None),
        view: str | None = Query(None),
        status: ImageStatus | None = Query(None),
        db: AsyncSession = Depends(get_async_db),
        current_user: User = Depends(get_current_user),
):
    image_service = ImageService(db)

    return await image_service.get_user_images(
        user_id=current_user.id,
        domain=domain,
        view=view,
        status=status
    )


@router.get("/{image_id}/url")
async def get_image_url(
        image_id: int,
        expires_in: int = Query(3600),
        db: AsyncSession = Depends(get_async_db),
        current_user: User = Depends(get_current_user),
):
    image_service = ImageService(db)

    image = await image_service.get_image(image_id, current_user.id)
    url = image_service.get_image_url(image, expires_in)

    return {
        "image_id": image_id,
        "url": url,
        "expires_in": expires_in
    }


@router.patch("/{image_id}", response_model=ImageOut)
async def update_image(
        image_id: int,
        payload: ImageUpdate,
        db: AsyncSession = Depends(get_async_db),
        current_user: User = Depends(get_current_user),
):
    image_service = ImageService(db)
    return await image_service.update_image(image_id, current_user.id, payload)


@router.delete("/{image_id}")
async def delete_image(
        image_id: int,
        db: AsyncSession = Depends(get_async_db),
        current_user: User = Depends(get_current_user),
):
    image_service = ImageService(db)
    await image_service.delete_image(image_id, current_user.id)

    return {
        "status": "deleted",
        "image_id": image_id,
        "message": "Image deleted successfully"
    }


@router.patch("/{image_id}/processed", response_model=ImageOut)
async def mark_image_processed(
        image_id: int,
        analysis_result: dict | str,
        db: AsyncSession = Depends(get_async_db),
        current_user: User = Depends(get_current_user),
):
    image_service = ImageService(db)

    await image_service.get_image(image_id, current_user.id)

    return await image_service.mark_processed(image_id, analysis_result)


@router.patch("/{image_id}/failed", response_model=ImageOut)
async def mark_image_failed(
        image_id: int,
        error_message: str | None = None,
        db: AsyncSession = Depends(get_async_db),
        current_user: User = Depends(get_current_user),
):
    image_service = ImageService(db)

    await image_service.get_image(image_id, current_user.id)

    return await image_service.mark_failed(image_id, error_message)

