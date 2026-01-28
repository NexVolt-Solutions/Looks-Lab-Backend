"""
Image service layer.
Handles image upload, processing, and management.
"""
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status, UploadFile

from app.models.image import Image, ImageStatus, ImageType
from app.schemas.image import ImageCreate, ImageUpdate
from app.core.storage import storage
from app.core.logging import logger


class ImageService:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def upload_image(
            self,
            file: UploadFile,
            user_id: int,
            domain: str | None = None,
            view: str | None = None,
            image_type: ImageType | None = None
    ) -> Image:
        try:
            destination_path = f"users/{user_id}/{domain or 'general'}/{file.filename}"

            file_path = storage.upload(
                file=file.file,
                destination_path=destination_path,
                content_type=file.content_type
            )

            image = Image(
                user_id=user_id,
                file_path=file_path,
                image_type=image_type or ImageType.uploaded,
                status=ImageStatus.pending,
                domain=domain,
                view=view,
                uploaded_at=datetime.now(timezone.utc)
            )

            self.db.add(image)
            await self.db.commit()
            await self.db.refresh(image)

            logger.info(f"Uploaded image {image.id} for user {user_id} ({domain}/{view})")
            return image

        except Exception as e:
            logger.error(f"Image upload failed for user {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Image upload failed"
            )

    async def create_image_record(self, payload: ImageCreate) -> Image:
        image = Image(
            user_id=payload.user_id,
            file_path=payload.file_path,
            image_type=payload.image_type,
            status=payload.status or ImageStatus.pending,
            analysis_result=payload.analysis_result,
            domain=payload.domain,
            view=payload.view,
            uploaded_at=datetime.now(timezone.utc),
        )

        self.db.add(image)
        await self.db.commit()
        await self.db.refresh(image)

        logger.info(f"Created image record {image.id} for user {payload.user_id}")
        return image

    async def get_image(self, image_id: int, user_id: int) -> Image:
        result = await self.db.execute(select(Image).where(Image.id == image_id))
        image = result.scalar_one_or_none()

        if not image:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Image not found"
            )

        if image.user_id != user_id:
            logger.warning(f"User {user_id} attempted to access image {image_id} owned by {image.user_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this image"
            )

        return image

    async def get_user_images(
            self,
            user_id: int,
            domain: str | None = None,
            view: str | None = None,
            status: ImageStatus | None = None
    ) -> list[Image]:
        query = select(Image).where(Image.user_id == user_id)

        if domain:
            query = query.where(Image.domain == domain)

        if view:
            query = query.where(Image.view == view)

        if status:
            query = query.where(Image.status == status)

        query = query.order_by(Image.uploaded_at.desc())

        result = await self.db.execute(query)
        return list(result.scalars().all())

    def get_image_url(self, image: Image, expires_in: int = 3600) -> str:
        return storage.get_url(image.file_path, expires_in)

    async def update_image(self, image_id: int, user_id: int, payload: ImageUpdate) -> Image:
        image = await self.get_image(image_id, user_id)

        if payload.analysis_result is not None:
            image.analysis_result = payload.analysis_result

        if payload.status is not None:
            image.status = payload.status

            if payload.status == ImageStatus.processed:
                image.processed_at = datetime.now(timezone.utc)

        if payload.image_type is not None:
            image.image_type = payload.image_type

        if payload.domain is not None:
            image.domain = payload.domain

        if payload.view is not None:
            image.view = payload.view

        image.updated_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(image)

        logger.info(f"Updated image {image_id} for user {user_id}")
        return image

    async def mark_processed(self, image_id: int, analysis_result: dict | str) -> Image:
        result = await self.db.execute(select(Image).where(Image.id == image_id))
        image = result.scalar_one_or_none()

        if not image:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Image not found"
            )

        image.status = ImageStatus.processed
        image.analysis_result = analysis_result
        image.processed_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(image)

        logger.info(f"Marked image {image_id} as processed")
        return image

    async def mark_failed(self, image_id: int, error_message: str | None = None) -> Image:
        result = await self.db.execute(select(Image).where(Image.id == image_id))
        image = result.scalar_one_or_none()

        if not image:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Image not found"
            )

        image.status = ImageStatus.failed
        image.processed_at = datetime.now(timezone.utc)

        if error_message:
            image.analysis_result = {"error": error_message}

        await self.db.commit()
        await self.db.refresh(image)

        logger.warning(f"Marked image {image_id} as failed: {error_message}")
        return image

    async def delete_image(self, image_id: int, user_id: int) -> None:
        image = await self.get_image(image_id, user_id)

        try:
            storage.delete(image.file_path)
        except Exception as e:
            logger.warning(f"Failed to delete file {image.file_path} from storage: {e}")

        await self.db.delete(image)
        await self.db.commit()

        logger.info(f"Deleted image {image_id} for user {user_id}")

