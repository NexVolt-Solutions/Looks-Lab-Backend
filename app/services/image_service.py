"""
Image service layer.
Handles image upload, processing, and management.
"""
from datetime import datetime, timezone

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

    # ── Upload ────────────────────────────────────────────────────

    async def upload_image(
        self,
        file: UploadFile,
        user_id: int,
        domain: str | None = None,
        view: str | None = None,
        image_type: ImageType | None = None
    ) -> Image:
        """
        Upload image to storage and create DB record.
        Uses BaseStorage.generate_path() for unique paths.
        """
        try:

            destination_path = BaseStorage.generate_path(
                user_id=user_id,
                domain=domain or "general",
                filename=file.filename or "upload.jpg",
                view=view
            )

            # Read content for file size tracking
            content = await file.read()
            file_size = len(content)
            await file.seek(0)

            # Upload to storage
            file_path = self._storage.upload(
                file=file.file,
                destination_path=destination_path,
                content_type=file.content_type
            )

            # Get initial URL
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
                uploaded_at=datetime.now(timezone.utc)
            )

            self.db.add(image)
            await self.db.commit()
            await self.db.refresh(image)

            logger.info(
                f"Uploaded image {image.id} for user {user_id} "
                f"({domain}/{view}) — {file_size / 1024:.1f}KB"
            )
            return image

        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                f"Image upload failed for user {user_id}: {e}",
                exc_info=settings.is_development
            )
            raise HTTPException(
                status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Image upload failed"
            )

    async def create_image_record(self, payload: ImageCreate) -> Image:
        """
        Create image DB record directly without uploading a file.
        Used when file is already in storage.
        """
        image = Image(
            user_id=payload.user_id,
            file_path=payload.file_path,
            s3_key=payload.s3_key,
            url=payload.url,
            mime_type=payload.mime_type,
            file_size=payload.file_size,
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

        logger.info(
            f"Created image record {image.id} "
            f"for user {payload.user_id}"
        )
        return image

    # ── Retrieval ─────────────────────────────────────────────────

    async def get_image(self, image_id: int, user_id: int) -> Image:
        """Get image by ID with ownership check."""
        result = await self.db.execute(
            select(Image).where(Image.id == image_id)
        )
        image = result.scalar_one_or_none()

        if not image:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Image not found"
            )

        if image.user_id != user_id:
            logger.warning(
                f"User {user_id} attempted to access image "
                f"{image_id} owned by {image.user_id}"
            )
            raise HTTPException(
                status_code=http_status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this image"
            )

        return image

    async def get_user_images(
        self,
        user_id: int,
        domain: str | None = None,
        view: str | None = None,
        image_status: ImageStatus | None = None
    ) -> list[Image]:
        """Get all images for a user with optional filters."""
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
        """
        Generate fresh pre-signed URL for image.
        Always generates fresh URL — stored URL may have expired.

        For CloudFront: returns permanent CDN URL directly.
        For S3: generates fresh pre-signed URL.
        """
        #  Fixed: always generate fresh URL — stored one may be expired
        # CloudFront URLs are permanent so get_url() returns CDN URL directly
        key = image.s3_key or image.file_path
        return self._storage.get_url(key, expires_in)

    # ── Update ────────────────────────────────────────────────────

    async def update_image(
        self,
        image_id: int,
        user_id: int,
        payload: ImageUpdate
    ) -> Image:
        """Update image metadata."""
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

    async def mark_processed(
        self,
        image_id: int,
        analysis_result: dict | str
    ) -> Image:
        """Mark image as successfully processed with analysis result."""
        result = await self.db.execute(
            select(Image).where(Image.id == image_id)
        )
        image = result.scalar_one_or_none()

        if not image:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Image not found"
            )

        image.status = ImageStatus.processed
        image.analysis_result = analysis_result
        image.processed_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(image)

        logger.info(f"Marked image {image_id} as processed")
        return image

    async def mark_failed(
        self,
        image_id: int,
        error_message: str | None = None
    ) -> Image:
        """Mark image as failed with dedicated error_message field."""
        result = await self.db.execute(
            select(Image).where(Image.id == image_id)
        )
        image = result.scalar_one_or_none()

        if not image:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Image not found"
            )

        image.status = ImageStatus.failed
        image.processed_at = datetime.now(timezone.utc)
        image.error_message = error_message

        await self.db.commit()
        await self.db.refresh(image)

        logger.warning(f"Marked image {image_id} as failed: {error_message}")
        return image

    # ── Delete ────────────────────────────────────────────────────

    async def delete_image(self, image_id: int, user_id: int) -> None:
        """Delete image from storage and database."""
        image = await self.get_image(image_id, user_id)


        storage_key = image.s3_key or image.file_path

        try:
            if storage_key:
                self._storage.delete(storage_key)
        except Exception as e:
            # Non-critical — log but continue with DB deletion
            logger.warning(
                f"Failed to delete file {storage_key} "
                f"from storage: {e}"
            )

        await self.db.delete(image)
        await self.db.commit()

        logger.info(f"Deleted image {image_id} for user {user_id}")

