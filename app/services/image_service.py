from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, UploadFile
from fastapi import status as http_status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import logger
from app.core.storage import get_storage, BaseStorage
from app.models.image import Image, ImageStatus, ImageType
from app.schemas.image import ImageCreate, ImageUpdate


class ImageService:

    def __init__(self, db: AsyncSession):
        self.db = db
        self._storage = get_storage()

    async def upload_image(
        self,
        file: UploadFile,
        user_id: int,
        domain: Optional[str] = None,
        view: Optional[str] = None,
        image_type: Optional[ImageType] = None,
    ) -> Image:
        try:
            destination_path = BaseStorage.generate_path(
                user_id=user_id,
                domain=domain or "general",
                filename=file.filename or "upload.jpg",
                view=view,
            )

            # Read once — use for both file_size and storage upload
            content = await file.read()
            file_size = len(content)

            import io
            file_path = self._storage.upload(
                file=io.BytesIO(content),
                destination_path=destination_path,
                content_type=file.content_type,
            )

            url = self._storage.get_url(file_path)

            image = Image(
                user_id=user_id,
                file_path=file_path,
                s3_key=destination_path,
                url=url,
                mime_type=file.content_type,
                file_size=file_size,
                image_type=image_type or ImageType.uploaded,
                status=ImageStatus.pending,
                domain=domain,
                view=view,
                uploaded_at=datetime.now(timezone.utc),
            )

            self.db.add(image)
            await self.db.commit()
            await self.db.refresh(image)

            logger.info(f"Uploaded image {image.id} for user {user_id} ({domain or 'general'}/{view or 'none'}) — {file_size / 1024:.1f}KB")
            return image

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Image upload failed for user {user_id}: {e}", exc_info=settings.is_development)
            raise HTTPException(status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Image upload failed")

    async def get_image(self, image_id: int, user_id: int) -> Image:
        result = await self.db.execute(select(Image).where(Image.id == image_id))
        image = result.scalar_one_or_none()

        if not image:
            raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Image not found")

        if image.user_id != user_id:
            logger.warning(f"User {user_id} attempted to access image {image_id} owned by {image.user_id}")
            raise HTTPException(status_code=http_status.HTTP_403_FORBIDDEN, detail="Not authorized to access this image")

        return image

    async def get_user_images(
        self,
        user_id: int,
        domain: Optional[str] = None,
        view: Optional[str] = None,
        image_status: Optional[ImageStatus] = None,
    ) -> list[Image]:
        query = select(Image).where(Image.user_id == user_id)

        if domain:
            query = query.where(Image.domain == domain)
        if view:
            query = query.where(Image.view == view)
        if image_status:
            query = query.where(Image.status == image_status)

        query = query.order_by(Image.uploaded_at.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    def get_image_url(self, image: Image, expires_in: int = 3600) -> str:
        key = image.s3_key or image.file_path
        return self._storage.get_url(key, expires_in)

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

        await self.db.commit()
        await self.db.refresh(image)

        logger.info(f"Updated image {image_id} for user {user_id}")
        return image

    async def mark_processed(self, image_id: int, analysis_result: dict | str) -> Image:
        result = await self.db.execute(select(Image).where(Image.id == image_id))
        image = result.scalar_one_or_none()

        if not image:
            raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Image not found")

        image.status = ImageStatus.processed
        image.analysis_result = analysis_result
        image.processed_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(image)

        logger.info(f"Marked image {image_id} as processed")
        return image

    async def mark_failed(self, image_id: int, error_message: Optional[str] = None) -> Image:
        result = await self.db.execute(select(Image).where(Image.id == image_id))
        image = result.scalar_one_or_none()

        if not image:
            raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Image not found")

        image.status = ImageStatus.failed
        image.processed_at = datetime.now(timezone.utc)
        image.error_message = error_message

        await self.db.commit()
        await self.db.refresh(image)

        logger.warning(f"Marked image {image_id} as failed: {error_message}")
        return image

    async def delete_image(self, image_id: int, user_id: int) -> None:
        image = await self.get_image(image_id, user_id)
        storage_key = image.s3_key or image.file_path

        try:
            if storage_key:
                self._storage.delete(storage_key)
        except Exception as e:
            logger.warning(f"Failed to delete file {storage_key} from storage: {e}")

        await self.db.delete(image)
        await self.db.commit()

        logger.info(f"Deleted image {image_id} for user {user_id}")
        
        