import asyncio
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.core.config import settings
from app.core.logging import logger
from app.enums import DomainEnum
from app.models.ai_job import AIJob
from app.models.domain import DomainAnswer, DomainQuestion
from app.models.image import Image, ImageStatus
from app.models.onboarding import OnboardingSession
from app.models.subscription import Subscription, SubscriptionStatus
from app.schemas.domain import DomainAnswerCreate, DomainFlowOut, DomainProgressOut, DomainQuestionOut
from app.schemas.insight import InsightCreate
from app.services.insight_service import InsightService
from app.services.progress_service import ProgressService
from app.utils import ai_task_manager

from app.ai.skin_care.processor import analyze_skincare
from app.ai.skin_care.config import SkincareAIConfig
from app.ai.hair_care.processor import analyze_haircare
from app.ai.hair_care.config import HaircareAIConfig
from app.ai.facial.processor import analyze_facial
from app.ai.facial.config import FacialAIConfig
from app.ai.diet.processor import analyze_diet
from app.ai.diet.config import DietAIConfig
from app.ai.height.processor import analyze_height
from app.ai.height.config import HeightAIConfig
from app.ai.workout.processor import analyze_workout
from app.ai.workout.config import WorkoutAIConfig
from app.ai.quit_porn.processor import analyze_quit_porn
from app.ai.quit_porn.config import QuitPornAIConfig
from app.ai.fashion.processor import analyze_fashion
from app.ai.fashion.config import FashionAIConfig


AI_CONFIGS = {
    "skincare":  SkincareAIConfig(),
    "haircare":  HaircareAIConfig(),
    "facial":    FacialAIConfig(),
    "diet":      DietAIConfig(),
    "height":    HeightAIConfig(),
    "workout":   WorkoutAIConfig(),
    "quit_porn": QuitPornAIConfig(),
    "fashion":   FashionAIConfig(),
}

AI_PROCESSORS = {
    "skincare":  analyze_skincare,
    "haircare":  analyze_haircare,
    "facial":    analyze_facial,
    "diet":      analyze_diet,
    "height":    analyze_height,
    "workout":   analyze_workout,
    "quit_porn": analyze_quit_porn,
    "fashion":   analyze_fashion,
}


class DomainService:
    IMAGE_DOMAINS = ("skincare", "haircare", "facial", "fashion")
    JOB_STATUS_PENDING = "pending"
    JOB_STATUS_PROCESSING = "processing"
    JOB_STATUS_COMPLETED = "completed"
    JOB_STATUS_FAILED = "failed"

    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_ai_job(self, user_id: int, domain: str) -> Optional[AIJob]:
        result = await self.db.execute(
            select(AIJob).where(AIJob.user_id == user_id, AIJob.domain == domain)
        )
        return result.scalar_one_or_none()

    def _job_to_task(self, job: Optional[AIJob]) -> Optional[dict[str, Any]]:
        if not job:
            return None

        result = None
        if job.result_payload:
            try:
                result = DomainFlowOut.model_validate(job.result_payload)
            except Exception as e:
                logger.warning(f"Could not deserialize AI job result for user {job.user_id} domain {job.domain}: {e}")

        return {
            "status": job.status,
            "result": result,
            "error": job.error_message,
            "submission_hash": job.submission_hash,
        }

    async def get_cached_ai_task(self, user_id: int, domain: str) -> Optional[dict[str, Any]]:
        job = await self._get_ai_job(user_id, domain)
        task = self._job_to_task(job)
        if task:
            return task
        return ai_task_manager.get_task(user_id, domain)

    async def get_submission_hash(self, user_id: int, domain: str) -> Optional[str]:
        job = await self._get_ai_job(user_id, domain)
        if job and job.submission_hash:
            return job.submission_hash
        return ai_task_manager.get_submission_hash(user_id, domain)

    async def remember_submission_hash(self, user_id: int, domain: str, submission_hash: str) -> None:
        stmt = pg_insert(AIJob).values(
            user_id=user_id,
            domain=domain,
            status=self.JOB_STATUS_PENDING,
            submission_hash=submission_hash,
        ).on_conflict_do_update(
            index_elements=[AIJob.user_id, AIJob.domain],
            set_={
                "submission_hash": submission_hash,
                "updated_at": datetime.now(timezone.utc),
            },
        )
        await self.db.execute(stmt)
        await self.db.commit()
        ai_task_manager.set_submission_hash(user_id, domain, submission_hash)

    async def clear_ai_job(self, user_id: int, domain: str) -> None:
        await self.db.execute(
            delete(AIJob).where(AIJob.user_id == user_id, AIJob.domain == domain)
        )
        await self.db.commit()
        ai_task_manager.clear_task(user_id, domain)

    async def _mark_job_processing(self, user_id: int, domain: str, submission_hash: Optional[str] = None) -> bool:
        if submission_hash is None:
            existing_job = await self._get_ai_job(user_id, domain)
            submission_hash = existing_job.submission_hash if existing_job else None

        now = datetime.now(timezone.utc)
        stmt = pg_insert(AIJob).values(
            user_id=user_id,
            domain=domain,
            status=self.JOB_STATUS_PROCESSING,
            submission_hash=submission_hash,
            result_payload=None,
            error_message=None,
            started_at=now,
            completed_at=None,
        ).on_conflict_do_update(
            index_elements=[AIJob.user_id, AIJob.domain],
            set_={
                "status": self.JOB_STATUS_PROCESSING,
                "submission_hash": submission_hash if submission_hash is not None else AIJob.submission_hash,
                "result_payload": None,
                "error_message": None,
                "started_at": now,
                "completed_at": None,
                "updated_at": now,
            },
            where=(AIJob.status != self.JOB_STATUS_PROCESSING),
        ).returning(AIJob.id)

        result = await self.db.execute(stmt)
        await self.db.commit()
        started = result.scalar_one_or_none() is not None

        if started:
            ai_task_manager.set_processing(user_id, domain)
            if submission_hash:
                ai_task_manager.set_submission_hash(user_id, domain, submission_hash)

        return started

    async def _mark_job_completed(self, user_id: int, domain: str, result: DomainFlowOut) -> None:
        now = datetime.now(timezone.utc)
        payload = result.model_dump(mode="json", exclude_none=True)
        stmt = pg_insert(AIJob).values(
            user_id=user_id,
            domain=domain,
            status=self.JOB_STATUS_COMPLETED,
            result_payload=payload,
            error_message=None,
            completed_at=now,
        ).on_conflict_do_update(
            index_elements=[AIJob.user_id, AIJob.domain],
            set_={
                "status": self.JOB_STATUS_COMPLETED,
                "result_payload": payload,
                "error_message": None,
                "completed_at": now,
                "updated_at": now,
            },
        )
        await self.db.execute(stmt)
        await self.db.commit()
        ai_task_manager.set_completed(user_id, domain, result)

    async def _mark_job_failed(self, user_id: int, domain: str, error: str) -> None:
        now = datetime.now(timezone.utc)
        stmt = pg_insert(AIJob).values(
            user_id=user_id,
            domain=domain,
            status=self.JOB_STATUS_FAILED,
            error_message=error[:1000],
            completed_at=now,
        ).on_conflict_do_update(
            index_elements=[AIJob.user_id, AIJob.domain],
            set_={
                "status": self.JOB_STATUS_FAILED,
                "error_message": error[:1000],
                "completed_at": now,
                "updated_at": now,
            },
        )
        await self.db.execute(stmt)
        await self.db.commit()
        ai_task_manager.set_failed(user_id, domain, error)

    async def _get_processing_image_ids(self, user_id: int, domain: str) -> list[int]:
        if domain not in self.IMAGE_DOMAINS:
            return []

        result = await self.db.execute(
            select(Image.id).where(
                Image.user_id == user_id,
                Image.domain == domain,
                Image.status == ImageStatus.processing,
            )
        )
        return [image_id for (image_id,) in result.all()]

    async def _mark_images_failed(self, image_ids: list[int], error: str) -> None:
        if not image_ids:
            return

        result = await self.db.execute(
            select(Image).where(Image.id.in_(image_ids))
        )
        images = result.scalars().all()
        now = datetime.now(timezone.utc)
        truncated_error = error[:512]

        for image in images:
            image.status = ImageStatus.failed
            image.error_message = truncated_error
            image.processed_at = now

        await self.db.commit()

    async def _reset_failed_images_for_retry(self, user_id: int, domain: str) -> None:
        if domain not in self.IMAGE_DOMAINS:
            return

        result = await self.db.execute(
            select(Image).where(
                Image.user_id == user_id,
                Image.domain == domain,
                Image.status == ImageStatus.failed,
            )
        )
        failed_images = result.scalars().all()

        if not failed_images:
            return

        for image in failed_images:
            image.status = ImageStatus.processing
            image.error_message = None
            image.processed_at = None

        await self.db.commit()

    async def check_domain_access(self, user_id: int, domain: str) -> None:
        if settings.BYPASS_SUBSCRIPTION_CHECK:
            logger.debug(f"Subscription check bypassed for user {user_id} domain {domain}")
            return

        session_result = await self.db.execute(
            select(OnboardingSession)
            .where(
                OnboardingSession.user_id == user_id,
                OnboardingSession.is_completed == True,  # noqa: E712
            )
            .order_by(OnboardingSession.created_at.desc())
            .limit(1)
        )
        session = session_result.scalars().first()

        if not session:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No onboarding session found")

        if session.selected_domain != domain:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Your selected domain is '{session.selected_domain}'"
            )

        if not session.is_paid:
            raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail="Payment required for domain access")

        sub_result = await self.db.execute(
            select(Subscription).where(Subscription.user_id == user_id)
            .order_by(Subscription.created_at.desc()).limit(1)
        )
        subscription = sub_result.scalars().first()

        if not subscription:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No active subscription found")

        if subscription.end_date and subscription.end_date < datetime.now(timezone.utc):
            raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail="Subscription expired")

        if subscription.status != SubscriptionStatus.active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Subscription not active (status: {subscription.status})"
            )

    async def get_domain_questions(self, domain: str) -> list[DomainQuestion]:
        result = await self.db.execute(
            select(DomainQuestion)
            .where(DomainQuestion.domain == domain)
            .order_by(DomainQuestion.seq.asc())
        )
        questions = list(result.scalars().all())

        if not questions:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No questions found for domain '{domain}'"
            )

        return questions

    async def save_answer(self, domain: str, payload: DomainAnswerCreate) -> DomainQuestion:
        result = await self.db.execute(
            select(DomainQuestion).where(DomainQuestion.id == payload.question_id)
        )
        question = result.scalar_one_or_none()

        if not question:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")

        result = await self.db.execute(
            select(DomainAnswer).where(
                DomainAnswer.user_id == payload.user_id,
                DomainAnswer.question_id == payload.question_id
            )
        )
        existing = result.scalar_one_or_none()
        now = datetime.now(timezone.utc)

        if existing:
            existing.answer = payload.answer
            existing.completed_at = now
        else:
            self.db.add(DomainAnswer(
                user_id=payload.user_id,
                question_id=payload.question_id,
                domain=domain,
                answer=payload.answer,
                completed_at=now
            ))

        await self.db.commit()
        return question

    async def get_user_answers(self, domain: str, user_id: int) -> list[dict]:
        result = await self.db.execute(
            select(DomainAnswer, DomainQuestion)
            .join(DomainQuestion, DomainAnswer.question_id == DomainQuestion.id)
            .where(DomainAnswer.user_id == user_id, DomainAnswer.domain == domain)
            .order_by(DomainQuestion.seq.asc())
        )
        return [
            {
                "question_id": question.id,
                "question":    question.question,
                "answer":      answer.answer,
                "answered_at": answer.completed_at,
            }
            for answer, question in result.all()
        ]

    async def reset_domain_answers(self, user_id: int, domain: str) -> None:
        await self.db.execute(
            delete(DomainAnswer).where(
                DomainAnswer.user_id == user_id,
                DomainAnswer.domain == domain,
            )
        )
        await self.db.commit()
        await self.clear_ai_job(user_id, domain)
        logger.info(f"Reset domain answers for {domain} (user {user_id})")

    async def calculate_progress(self, domain: str, user_id: int) -> DomainProgressOut:
        questions = await self.get_domain_questions(domain)

        result = await self.db.execute(
            select(DomainAnswer).where(
                DomainAnswer.user_id == user_id,
                DomainAnswer.domain == domain
            )
        )
        answers = list(result.scalars().all())
        answered_ids = [a.question_id for a in answers]
        total = len(questions)
        answered = len(answered_ids)

        sub_result2 = await self.db.execute(
            select(Subscription).where(Subscription.user_id == user_id)
            .order_by(Subscription.created_at.desc()).limit(1)
        )
        subscription = sub_result2.scalars().first()
        subscription_status = None

        if subscription:
            if subscription.end_date and subscription.end_date < datetime.now(timezone.utc):
                subscription_status = SubscriptionStatus.expired
            else:
                subscription_status = subscription.status

        return DomainProgressOut(
            user_id=user_id,
            domain=domain,
            progress={"total": total, "answered": answered, "completed": answered == total and total > 0},
            answered_questions=answered_ids,
            total_questions=total,
            progress_percent=(answered / total * 100) if total else 0.0,
            subscription_status=subscription_status
        )

    async def next_or_complete(self, user_id: int, domain: str, submission_hash: Optional[str] = None) -> DomainFlowOut:
        questions = await self.get_domain_questions(domain)

        result = await self.db.execute(
            select(DomainAnswer.question_id).where(
                DomainAnswer.user_id == user_id,
                DomainAnswer.domain == domain
            )
        )
        answered_ids = {qid for (qid,) in result.all()}

        # Still has unanswered questions -> return next question
        for idx, q in enumerate(questions):
            if q.id not in answered_ids:
                next_q = questions[idx + 1] if idx + 1 < len(questions) else None
                return DomainFlowOut(
                    status="ok",
                    current=DomainQuestionOut.model_validate(q),
                    next=DomainQuestionOut.model_validate(next_q) if next_q else None,
                    progress=await self.calculate_progress(domain, user_id),
                )

        # All questions answered -> check if AI already running
        task = await self.get_cached_ai_task(user_id, domain)

        if task and task["status"] == self.JOB_STATUS_PROCESSING:
            # AI is still running -> return processing immediately
            logger.info(f"AI still processing for {domain} (user {user_id}) -- returning processing status")
            return DomainFlowOut(
                status="processing",
                current=None,
                next=None,
                progress=await self.calculate_progress(domain, user_id),
                redirect="processing",
            )

        if task and task["status"] == self.JOB_STATUS_COMPLETED and task["result"] is not None:
            # AI finished -> return cached result
            logger.info(f"Returning cached AI result for {domain} (user {user_id})")
            return task["result"]

        if task and task["status"] == self.JOB_STATUS_FAILED:
            # Previous attempt failed -> clear and retry
            await self._reset_failed_images_for_retry(user_id, domain)
            await self.clear_ai_job(user_id, domain)

        # No task running -> start AI in background, return processing immediately
        started = await self._mark_job_processing(user_id, domain, submission_hash=submission_hash)
        progress = await self.calculate_progress(domain, user_id)

        if not started:
            logger.info(f"AI already processing for {domain} (user {user_id}) -- returning processing status")
            return DomainFlowOut(
                status="processing",
                current=None,
                next=None,
                progress=progress,
                redirect="processing",
            )

        # Launch background task (non-blocking)
        asyncio.create_task(
            self._run_ai_in_background(user_id, domain)
        )

        logger.info(f"AI background task started for {domain} (user {user_id}) -- returning processing status")
        return DomainFlowOut(
            status="processing",
            current=None,
            next=None,
            progress=progress,
            redirect="processing",
        )

    async def _run_ai_in_background(self, user_id: int, domain: str) -> None:
        """Runs AI processing in background with its own DB session."""
        from app.core.database import AsyncSessionLocal
        processing_image_ids: list[int] = []
        try:
            async with AsyncSessionLocal() as db:
                service = DomainService(db)
                processing_image_ids = await service._get_processing_image_ids(user_id, domain)
                result = await service._process_ai_completion(user_id, domain)
                await service._mark_job_completed(user_id, domain, result)
                logger.info(f"Background AI task completed for {domain} (user {user_id})")
        except Exception as e:
            async with AsyncSessionLocal() as db:
                service = DomainService(db)
                await service._mark_images_failed(processing_image_ids, str(e))
                await service._mark_job_failed(user_id, domain, str(e))
            logger.error(f"Background AI task failed for {domain} (user {user_id}): {e}", exc_info=True)

    _DOMAIN_ICONS: dict[str, str] = {
        "skincare":  "https://api.lookslabai.com/static/icons/SkinCare.jpg",
        "haircare":  "https://api.lookslabai.com/static/icons/Hair.png",
        "workout":   "https://api.lookslabai.com/static/icons/Workout.jpg",
        "diet":      "https://api.lookslabai.com/static/icons/Diet.jpg",
        "facial":    "https://api.lookslabai.com/static/icons/Facial.jpg",
        "fashion":   "https://api.lookslabai.com/static/icons/Fashion.png",
        "height":    "https://api.lookslabai.com/static/icons/Height.jpg",
        "quit_porn": "https://api.lookslabai.com/static/icons/QuitPorn.jpg",
    }

    async def get_all_domains_progress(self, user_id: int) -> dict[str, Any]:
        progress_overview = []

        for domain in DomainEnum.values():
            try:
                progress = await self.calculate_progress(domain, user_id)
                progress_overview.append({
                    "domain":             domain,
                    "icon_url":           self._DOMAIN_ICONS.get(domain),
                    "progress_percent":   round(progress.progress_percent, 1),
                    "answered_questions": len(progress.answered_questions),
                    "total_questions":    progress.total_questions,
                    "is_completed":       progress.progress.get("completed", False),
                })
            except Exception as e:
                if not isinstance(e, HTTPException):
                    logger.error(f"Error getting progress for domain {domain}, user {user_id}: {e}", exc_info=settings.is_development)
                progress_overview.append({
                    "domain":             domain,
                    "icon_url":           self._DOMAIN_ICONS.get(domain),
                    "progress_percent":   0.0,
                    "answered_questions": 0,
                    "total_questions":    0,
                    "is_completed":       False,
                })

        average = sum(d["progress_percent"] for d in progress_overview) / len(progress_overview) if progress_overview else 0.0

        return {
            "user_id":           user_id,
            "domains":           progress_overview,
            "overall_average":   round(average, 2),
            "domains_started":   sum(1 for d in progress_overview if d["progress_percent"] > 0),
            "domains_completed": sum(1 for d in progress_overview if d["is_completed"]),
            "total_domains":     len(progress_overview),
        }

    async def _get_answers_with_context(self, domain: str, user_id: int) -> list[dict]:
        result = await self.db.execute(
            select(DomainAnswer, DomainQuestion)
            .join(DomainQuestion, DomainAnswer.question_id == DomainQuestion.id)
            .where(DomainAnswer.user_id == user_id, DomainAnswer.domain == domain)
            .order_by(DomainQuestion.seq.asc())
        )
        return [
            {"step": question.seq, "question": question.question, "answer": answer.answer}
            for answer, question in result.all()
        ]

    async def _get_domain_images(self, user_id: int, domain: str) -> list[dict]:
        try:
            result = await self.db.execute(
                select(Image).where(Image.user_id == user_id, Image.domain == domain)
            )
            return [
                {
                    "id": img.id,
                    "view": img.view,
                    "url": img.url or img.s3_key,
                    "status": img.status,
                }
                for img in result.scalars().all()
            ]
        except Exception as e:
            logger.warning(f"Could not fetch images for {domain} (user {user_id}): {e}")
            return []

    def _extract_score(self, domain: str, ai_output: dict) -> Optional[float]:
        if not ai_output:
            return None

        # For workout: derive score from intensity
        if domain == "workout":
            attributes = ai_output.get("attributes", {})
            if isinstance(attributes, dict):
                intensity = str(attributes.get("intensity", "")).lower()
                intensity_score_map = {"low": 40.0, "moderate": 65.0, "high": 85.0}
                return intensity_score_map.get(intensity, 60.0)

        # For quit_porn: derive score from progress_tracking.recovery_score
        if domain == "skincare":
            routine = _get("routine") or {}
            return DomainFlowOut(
                status="completed",
                redirect="completed_flow",
                progress=progress,
                ai_attributes=_get("attributes"),
                ai_health=_get("health"),
                ai_concerns=_get("concerns"),
                ai_message=_get("motivational_message"),
                ai_remedies=_get("remedies"),
                ai_products=_get("products"),
                ai_routine={
                    "today": routine.get("today") or [],
                    "night": routine.get("night") or [],
                    "morning": routine.get("today") or [],
                    "evening": routine.get("night") or [],
                },
            )

        if domain == "quit_porn":
            progress = ai_output.get("progress_tracking", {})
            if isinstance(progress, dict):
                raw = str(progress.get("recovery_score", "")).replace("%", "").replace("+", "").strip()
                try:
                    return min(max(float(raw), 0.0), 100.0)
                except ValueError:
                    return 50.0

        score_field_map = {
            "skincare":  "health_score",
            "haircare":  "health_score",
            "facial":    "health_score",
            "diet":      "health_score",
            "height":    "health_score",
            "fashion":   "health_score",
        }

        field = score_field_map.get(domain, "health_score")
        score = ai_output.get(field)

        if score is None:
            health = ai_output.get("health", {})
            if isinstance(health, dict):
                score = health.get("score") or health.get("health_score") or health.get("overall_score")

        if score is None:
            attributes = ai_output.get("attributes", {})
            if isinstance(attributes, dict):
                score = attributes.get("overall_score") or attributes.get("score")

        if score is None:
            progress = ai_output.get("progress_tracking", {})
            if isinstance(progress, dict):
                raw = str(progress.get("recovery_score", "")).replace("%", "").strip()
                try:
                    score = float(raw) if raw else None
                except ValueError:
                    pass

        if score is not None:
            try:
                return min(max(float(score), 0.0), 100.0)
            except (TypeError, ValueError):
                return None

        return None

    async def _process_ai_completion(self, user_id: int, domain: str) -> DomainFlowOut:
        progress = await self.calculate_progress(domain, user_id)
        answers_ctx = await self._get_answers_with_context(domain, user_id)
        images = await self._get_domain_images(user_id, domain)
        image_ids_used = [img["id"] for img in images if img.get("id") is not None]

        config = AI_CONFIGS.get(domain)
        processor = AI_PROCESSORS.get(domain)
        ai_output = None

        if config and processor:
            if len(answers_ctx) < config.MIN_ANSWERS_REQUIRED:
                logger.warning(f"Domain {domain}: only {len(answers_ctx)} answers, need {config.MIN_ANSWERS_REQUIRED} (user {user_id})")
            elif config.REQUIRE_IMAGES and not images:
                logger.warning(f"Domain {domain} requires images but none found for user {user_id}")
            else:
                try:
                    ai_output = processor(answers_ctx, images)
                    logger.info(f"AI processing complete for {domain} (user {user_id})")
                except Exception as e:
                    logger.error(f"AI processing failed for {domain} (user {user_id}): {e}", exc_info=settings.is_development)

        if ai_output:
            score = self._extract_score(domain, ai_output)

            try:
                await InsightService(self.db).create_or_update_insight(InsightCreate(
                    user_id=user_id,
                    category=domain,
                    content=ai_output,
                    source="ai",
                    score=score,
                ))
            except Exception as e:
                logger.error(f"Failed to save insight for {domain} (user {user_id}): {e}", exc_info=settings.is_development)

            if score is not None:
                try:
                    await ProgressService(self.db).save_score_snapshot(user_id, domain, score)
                except Exception as e:
                    logger.error(f"Failed to save score snapshot for {domain} (user {user_id}): {e}", exc_info=settings.is_development)

            # For image-based domains: update image rows from pending -> processed with analysis_result
            if domain in ("skincare", "haircare", "facial", "fashion"):
                try:
                    from app.models.image import Image, ImageStatus
                    from sqlalchemy import select as sa_select
                    if not image_ids_used:
                        logger.info(f"No uploaded images to finalize for {domain} (user {user_id})")
                        processing_images = []
                    else:
                        img_result = await self.db.execute(
                            sa_select(Image).where(
                                Image.id.in_(image_ids_used),
                                Image.user_id == user_id,
                                Image.domain == domain,
                                Image.status == ImageStatus.processing,
                            )
                        )
                        processing_images = img_result.scalars().all()

                    # Build real bullet points from AI concerns output
                    concerns = ai_output.get("concerns", {})
                    points = []
                    if isinstance(concerns, dict):
                        for key, val in concerns.items():
                            if isinstance(val, dict):
                                label = val.get("label", "")
                                if label and label.lower() not in ("none", "normal"):
                                    points.append(f"{key.replace(chr(95), chr(32)).title()}: {label}")
                    if not points:
                        points = ["Analysis complete. Check your routine for personalized recommendations."]

                    analysis_result = {"points": points}

                    for img in processing_images:
                        img.status = ImageStatus.processed
                        img.analysis_result = analysis_result
                        from datetime import datetime, timezone as tz
                        img.processed_at = datetime.now(tz.utc)

                    if processing_images:
                        await self.db.commit()
                        logger.info(f"Updated {len(processing_images)} images to processed for {domain} (user {user_id})")
                except Exception as e:
                    logger.error(f"Failed to update image status for {domain} (user {user_id}): {e}", exc_info=settings.is_development)

        def _get(key: str) -> Optional[Any]:
            return ai_output.get(key) if ai_output else None

        if domain == "skincare":
            routine = _get("routine") or {}
            return DomainFlowOut(
                status="completed",
                redirect="completed_flow",
                progress=progress,
                ai_attributes=_get("attributes"),
                ai_health=_get("health"),
                ai_concerns=_get("concerns"),
                ai_message=_get("motivational_message"),
                ai_remedies=_get("remedies"),
                ai_products=_get("products"),
                ai_routine={
                    "today": routine.get("today") or [],
                    "night": routine.get("night") or [],
                    "morning": routine.get("today") or [],
                    "evening": routine.get("night") or [],
                },
            )

        if domain == "quit_porn":
            progress_tracking = _get("progress_tracking") or {}
            recovery_path = _get("recovery_path") or {}
            # Ensure daily_tasks is always a list
            daily_tasks = recovery_path.get("daily_tasks") or []
            streak = recovery_path.get("streak") or {
                "current_streak": 0,
                "longest_streak": 0,
                "next_goal": 7,
                "streak_message": "Today is day one. Let's make it count!"
            }
            return DomainFlowOut(
                status="completed",
                redirect="completed_flow",
                progress=progress,
                ai_attributes=_get("attributes"),
                ai_message=_get("motivational_message"),
                ai_progress={
                    "consistency": progress_tracking.get("consistency", "42%"),
                    "recovery_score": progress_tracking.get("recovery_score", "58%"),
                    "recovery_checklist": progress_tracking.get("recovery_checklist") or [
                        "Set your daily intention",
                        "Evening reflection",
                        "Productive alone time",
                        "Connect with someone",
                    ],
                },
                ai_recovery={
                    "streak": streak,
                    "daily_tasks": daily_tasks,
                },
            )

        if domain == "workout":
            # Build ai_progress with AI values + static recovery checklist labels
            attributes = _get("attributes") or {}
            intensity = str(attributes.get("intensity", "Moderate")).lower()
            strength_map = {"low": "+5%", "moderate": "+12%", "high": "+20%"}
            strength_gain = strength_map.get(intensity, "+12%")
            progress_tracking = _get("progress_tracking") or {}
            ai_progress = {
                "weekly_calories": progress_tracking.get("weekly_calories", "2300"),
                "consistency": progress_tracking.get("fitness_consistency", "85%"),
                "strength_gain": strength_gain,
                "fitness_consistency": progress_tracking.get("fitness_consistency", "85%"),
                "calorie_balance": "85%",
                "hydration": "85%",
                "recovery_checklist": [
                    "Got 7+ hours of sleep",
                    "Drank 8+ glasses of water",
                    "Stretched for 10 minutes",
                    "Took a rest if needed",
                ],
            }
            return DomainFlowOut(
                status="completed",
                redirect="completed_flow",
                ai_attributes=_get("attributes"),
                ai_progress=ai_progress,
            )

        return DomainFlowOut(
            status="completed",
            current=None,
            next=None,
            progress=progress,
            redirect="completed_flow",
            ai_attributes=_get("attributes"),
            ai_health=_get("health"),
            ai_concerns=_get("concerns"),
            ai_message=_get("motivational_message"),
            ai_remedies=_get("remedies"),
            ai_products=_get("products"),
            ai_routine=_get("routine"),
            ai_exercises=_get("daily_exercises"),
            ai_progress=_get("progress_tracking"),
            ai_today_focus=_get("today_focus"),
            ai_workout_summary=_get("workout_summary"),
            ai_nutrition=_get("nutrition_targets"),
            ai_recovery=_get("recovery_path"),
            ai_features=_get("feature_scores"),
        )
        
        
