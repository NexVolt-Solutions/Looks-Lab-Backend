from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, UploadFile
from fastapi import status as http_status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.file_validation import normalize_filename_for_mime
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
        detected_mime_type: Optional[str] = None,
    ) -> Image:
        file_path: Optional[str] = None
        try:
            effective_mime_type = detected_mime_type or file.content_type or "image/jpeg"
            normalized_filename = normalize_filename_for_mime(file.filename, effective_mime_type)
            destination_path = BaseStorage.generate_path(
                user_id=user_id,
                domain=domain or "general",
                filename=normalized_filename,
                view=view,
            )

            content = await file.read()
            file_size = len(content)

            import io
            file_path = self._storage.upload(
                file=io.BytesIO(content),
                destination_path=destination_path,
                content_type=effective_mime_type,
            )

            url = self._storage.get_url(file_path)

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
                mime_type=effective_mime_type,
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

            logger.info(
                f"Uploaded image {image.id} for user {user_id} ({domain or 'general'}/{view or 'none'}) - {file_size / 1024:.1f}KB"
            )

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

    def get_image_url(self, image: Image) -> str:
        return image.url or ""

    async def get_user_images(
        self,
        user_id: int,
        domain: Optional[str] = None,
        view: Optional[str] = None,
        image_status: Optional[ImageStatus] = None,
    ) -> list[Image]:
        query = select(Image).where(Image.user_id == user_id).order_by(Image.uploaded_at.desc())

        if domain:
            query = query.where(Image.domain == domain)
        if view:
            query = query.where(Image.view == view)
        if image_status:
            query = query.where(Image.status == image_status)

        result = await self.db.execute(query)
        images = list(result.scalars().all())

        if domain in ("skincare", "haircare", "facial", "fashion") and domain and not view:
            latest_per_view: dict[str, Image] = {}
            for image in images:
                view_key = image.view or "unknown"
                if view_key not in latest_per_view:
                    latest_per_view[view_key] = image
            return list(latest_per_view.values())

        return images

    async def get_image(self, image_id: int, user_id: int) -> Image:
        result = await self.db.execute(select(Image).where(Image.id == image_id))
        image = result.scalar_one_or_none()

        if not image:
            raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Image not found")
        if image.user_id != user_id:
            raise HTTPException(status_code=http_status.HTTP_403_FORBIDDEN, detail="Not authorized to access this image")

        return image

    async def update_image(self, image_id: int, user_id: int, payload: ImageUpdate) -> Image:
        image = await self.get_image(image_id, user_id)

        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(image, field, value)

        await self.db.commit()
        await self.db.refresh(image)
        logger.info(f"Updated image {image_id} for user {user_id}")
        return image

    async def delete_image(self, image_id: int, user_id: int) -> None:
        image = await self.get_image(image_id, user_id)

        try:
            if image.file_path:
                self._storage.delete(image.file_path)
        except Exception as e:
            logger.warning(f"Could not delete storage object for image {image_id}: {e}")

        await self.db.delete(image)
        await self.db.commit()
        logger.info(f"Deleted image {image_id} for user {user_id}")

    async def mark_failed(self, image_id: int, error_message: str) -> None:
        result = await self.db.execute(select(Image).where(Image.id == image_id))
        image = result.scalar_one_or_none()
        if not image:
            return

        image.status = ImageStatus.failed
        image.error_message = error_message[:512]
        image.processed_at = datetime.now(timezone.utc)
        await self.db.commit()

    async def _set_image_error_message(self, image_id: int, error_message: Optional[str]) -> None:
        result = await self.db.execute(select(Image).where(Image.id == image_id))
        image = result.scalar_one_or_none()
        if not image:
            return

        image.error_message = error_message[:512] if error_message else None
        await self.db.commit()

    async def _run_quick_analysis(self, image_id: int, image_url: str, domain: str, user_id: int) -> None:
        try:
            import base64
            import json
            import asyncio
            import httpx
            from google import genai
            from google.genai import types
            from app.ai.quick_analysis_prompt import QUICK_ANALYSIS_PROMPTS

            prompt = QUICK_ANALYSIS_PROMPTS.get(domain)
            if not prompt:
                return

            timeout = httpx.Timeout(15.0, connect=10.0)
            async with httpx.AsyncClient(timeout=timeout) as client_http:
                resp = await client_http.get(image_url)
                resp.raise_for_status()
                image_bytes = resp.content
                content_type = resp.headers.get("content-type", "image/jpeg")

            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(
                None,
                lambda: client.models.generate_content(
                    model=settings.GEMINI_MODEL,
                    contents=[
                        types.Part.from_bytes(data=image_bytes, mime_type=content_type),
                        prompt,
                    ],
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                    ),
                ),
            )

            text = getattr(response, "text", None) or "{}"
            data = json.loads(text) if text else {}
            points = data.get("points") if isinstance(data, dict) else None
            if not isinstance(points, list):
                logger.warning(f"Quick analysis returned no usable points for image {image_id} ({domain})")
                await self._set_image_error_message(image_id, "Quick analysis returned no usable preview points")
                return
            cleaned = [str(p).strip() for p in points if str(p).strip()][:5]
            if not cleaned:
                logger.warning(f"Quick analysis returned empty points for image {image_id} ({domain})")
                await self._set_image_error_message(image_id, "Quick analysis returned empty preview points")
                return

            result = await self.db.execute(select(Image).where(Image.id == image_id))
            image = result.scalar_one_or_none()
            if image and image.user_id == user_id:
                image.analysis_result = {"points": cleaned}
                image.error_message = None
                await self.db.commit()
                logger.info(f"Saved quick analysis for image {image_id} ({domain})")
        except Exception as e:
            logger.warning(f"Quick analysis failed for image {image_id} ({domain}): {e}")
            await self._set_image_error_message(image_id, str(e))
