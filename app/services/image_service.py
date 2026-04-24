from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, UploadFile
from fastapi import status as http_status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import logger
from app.core.storage import get_storage, BaseStorage
from app.models.ai_job import AIJob
from app.models.image import Image, ImageStatus, ImageType
from app.schemas.image import ImageUpdate


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
        file_path: Optional[str] = None
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

            # Image-based domains start as processing (AI will analyze)
            # Non-domain images start as pending
            initial_status = (
                ImageStatus.processing
                if domain in ("skincare", "haircare", "facial", "fashion")
                else ImageStatus.pending
            )

            image = Image(
                user_id=user_id,
                file_path=file_path,
                s3_key=destination_path,
                url=url,
                mime_type=file.content_type,
                file_size=file_size,
                image_type=image_type or ImageType.uploaded,
                status=initial_status,
                domain=domain,
                view=view,
                uploaded_at=datetime.now(timezone.utc),
            )

            self.db.add(image)
            await self.db.commit()
            await self.db.refresh(image)

            logger.info(f"Uploaded image {image.id} for user {user_id} ({domain or 'general'}/{view or 'none'}) — {file_size / 1024:.1f}KB")

            # Clear AI task state so the next domain flow re-runs with the new images.
            if domain in ("skincare", "haircare", "facial", "fashion"):
                try:
                    await self.db.execute(
                        delete(AIJob).where(AIJob.user_id == user_id, AIJob.domain == domain)
                    )
                    await self.db.commit()
                    from app.utils import ai_task_manager
                    ai_task_manager.clear_task(user_id, domain)
                    logger.info(f"Cleared AI task state for {domain} (user {user_id}) - will re-run with new images")
                except Exception as e:
                    logger.warning(f"Failed to clear AI task state for {domain} (user {user_id}): {e}")

                # Run quick vision analysis in background — keep reference to prevent GC
                import asyncio
                image_url_for_analysis = image.url or ""
                if image_url_for_analysis:
                    _quick_task = asyncio.create_task(
                        self._run_quick_analysis(image.id, image_url_for_analysis, domain, user_id)
                    )
                    _quick_task.add_done_callback(
                        lambda t: t.exception() if not t.cancelled() else None
                    )
                else:
                    logger.warning(f"No URL available for quick analysis on image {image.id}")

            return image

        except HTTPException:
            raise
        except Exception as e:
            if file_path:
                try:
                    self._storage.delete(file_path)
                    logger.warning(f"Rolled back uploaded file for user {user_id}: {file_path}")
                except Exception as cleanup_error:
                    logger.warning(f"Failed to clean up uploaded file {file_path}: {cleanup_error}")
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

    def get_image_url(self, image: Image) -> str:
        if image.url:
            return image.url

        storage_key = image.s3_key or image.file_path
        if not storage_key:
            raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Image URL unavailable")

        return self._storage.get_url(storage_key)

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
        all_images = list(result.scalars().all())

        # For image-based domains: return only the latest image per view
        # This prevents Flutter from getting confused by duplicate uploads
        if domain and domain in ("skincare", "haircare", "facial", "fashion") and not view and not image_status:
            seen_views = set()
            latest_per_view = []
            for img in all_images:  # already ordered by uploaded_at desc
                if img.view not in seen_views:
                    seen_views.add(img.view)
                    latest_per_view.append(img)

            return latest_per_view

        return all_images

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

    async def _run_quick_analysis(self, image_id: int, image_url: str, domain: str, user_id: int) -> None:
        """Run quick Gemini vision analysis on uploaded image to generate real bullets."""
        try:
            import asyncio
            import json
            import httpx
            import google.generativeai as genai
            from app.core.config import settings
            from app.ai.quick_analysis_prompt import get_quick_prompt
            from app.core.database import AsyncSessionLocal

            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(image_url)
                if resp.status_code != 200:
                    await self._set_image_error_message(image_id, f"Quick analysis fetch failed with status {resp.status_code}")
                    logger.warning(f"Quick analysis could not fetch image {image_id} (status={resp.status_code})")
                    return
                image_bytes = resp.content
                content_type = resp.headers.get("content-type", "image/jpeg")

            prompt = get_quick_prompt(domain)
            image_part = {"mime_type": content_type, "data": image_bytes}

            loop = asyncio.get_running_loop()

            def _call_gemini():
                mdl = genai.GenerativeModel(settings.GEMINI_MODEL)
                return mdl.generate_content(
                    [prompt, image_part],
                    generation_config=genai.GenerationConfig(
                        temperature=0.3,
                        max_output_tokens=300,
                        response_mime_type="application/json",
                    ),
                    request_options={"timeout": 15}
                )

            response = await loop.run_in_executor(None, _call_gemini)

            if not response or not response.text:
                await self._set_image_error_message(image_id, "Quick analysis returned an empty response")
                return

            text = response.text.strip()
            data = json.loads(text)
            points = data.get("points", [])

            if not points or not isinstance(points, list):
                await self._set_image_error_message(image_id, "Quick analysis returned no usable preview points")
                logger.warning(f"Quick analysis returned no usable points for image {image_id}")
                return

            async with AsyncSessionLocal() as db:
                from sqlalchemy import select as sa_select
                result = await db.execute(sa_select(Image).where(Image.id == image_id))
                img = result.scalar_one_or_none()
                if img and img.status == ImageStatus.processing:
                    img.analysis_result = {"points": [str(p) for p in points[:5]], "is_preview": True}
                    img.error_message = None
                    await db.commit()
                    logger.info(f"Quick vision analysis complete for image {image_id} ({domain}) user {user_id}")

        except Exception as e:
            await self._set_image_error_message(image_id, f"Quick analysis failed: {str(e)[:400]}")
            logger.warning(f"Quick analysis failed for image {image_id}: {e}")

    async def _set_image_error_message(self, image_id: int, error_message: str) -> None:
        from app.core.database import AsyncSessionLocal

        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Image).where(Image.id == image_id))
            image = result.scalar_one_or_none()
            if not image:
                return

            image.error_message = error_message[:512]
            await db.commit()

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

        