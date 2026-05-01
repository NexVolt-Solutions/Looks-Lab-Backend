import asyncio
from datetime import date, datetime, timezone
from typing import Any, Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import logger
from app.enums import DomainEnum
from app.models.domain import DomainAnswer, DomainQuestion
from app.models.image import Image
from app.models.insight import Insight
from app.models.onboarding import OnboardingSession
from app.models.subscription import Subscription, SubscriptionStatus
from app.models.workout_completion import WorkoutCompletion
from app.schemas.domain import DomainAnswerCreate, DomainFlowOut, DomainProgressOut, DomainQuestionOut
from app.schemas.insight import InsightCreate
from app.services.insight_service import InsightService
from app.services.progress_service import ProgressService
from app.utils import ai_task_manager
from app.utils.domain_score_utils import extract_domain_score

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

    def __init__(self, db: AsyncSession):
        self.db = db

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
        from sqlalchemy import delete
        await self.db.execute(
            delete(DomainAnswer).where(
                DomainAnswer.user_id == user_id,
                DomainAnswer.domain == domain,
            )
        )
        await self.db.commit()
        await ai_task_manager.clear_task(user_id, domain)
        logger.info(f"Reset domain answers for {domain} (user {user_id})")

    async def get_submission_hash(self, user_id: int, domain: str) -> Optional[str]:
        return await ai_task_manager.get_submission_hash(user_id, domain)

    async def remember_submission_hash(self, user_id: int, domain: str, submission_hash: str) -> None:
        await ai_task_manager.set_submission_hash(user_id, domain, submission_hash)

    async def get_cached_ai_task(self, user_id: int, domain: str) -> Optional[dict[str, Any]]:
        return await ai_task_manager.get_task(user_id, domain)

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

    async def next_or_complete(
        self,
        user_id: int,
        domain: str,
        submission_hash: Optional[str] = None,
    ) -> DomainFlowOut:
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
                status_value = "in_progress" if domain == "fashion" else "ok"
                return DomainFlowOut(
                    status=status_value,
                    current=DomainQuestionOut.model_validate(q),
                    next=DomainQuestionOut.model_validate(next_q) if next_q else None,
                    progress=await self.calculate_progress(domain, user_id),
                )

        progress = await self.calculate_progress(domain, user_id)

        # Fashion contract: both required scans must exist before AI processing can start.
        if domain == "fashion":
            front_ready, back_ready = await self._fashion_required_scans_ready(user_id)
            if not (front_ready and back_ready):
                return DomainFlowOut(
                    status="pending",
                    current=None,
                    next=None,
                    progress=progress,
                    redirect="review_scans",
                )

        # Facial contract: front/right/left scans must exist before AI processing can start.
        if domain == "facial":
            front_ready, right_ready, left_ready = await self._facial_required_scans_ready(user_id)
            if not (front_ready and right_ready and left_ready):
                return DomainFlowOut(
                    status="pending",
                    current=None,
                    next=None,
                    progress=progress,
                    redirect="review_scans",
                )

        fresh_ai_output = await self._get_fresh_completed_ai_output(user_id, domain)
        if fresh_ai_output:
            logger.info(f"Returning persisted completed flow for {domain} (user {user_id})")
            return await self._build_completed_flow(user_id, domain, progress, fresh_ai_output)

        # All questions answered -> check if AI already running
        task = await ai_task_manager.get_task(user_id, domain)

        if task and task["status"] == "processing":
            # Check if task has timed out (Gemini hung or silently failed)
            if await ai_task_manager.is_timed_out(user_id, domain, timeout_seconds=90):
                logger.warning(f"AI task timed out for {domain} (user {user_id}) — clearing and retrying")
                await ai_task_manager.clear_task(user_id, domain)
                # Fall through to re-launch AI below
            else:
                # AI is still running -> return processing immediately
                logger.info(f"AI still processing for {domain} (user {user_id}) -- returning processing status")
                return DomainFlowOut(
                    status="processing",
                    current=None,
                    next=None,
                    progress=progress,
                    redirect="processing",
                )

        if task and task["status"] == "completed":
            # AI finished -> return cached result
            if task.get("result") is not None:
                logger.info(f"Returning cached AI result for {domain} (user {user_id})")
                return DomainFlowOut.model_validate(task["result"])

            logger.warning(f"Completed AI task had no result for {domain} (user {user_id}) — clearing and rebuilding state")
            await ai_task_manager.clear_task(user_id, domain)
            fresh_ai_output = await self._get_fresh_completed_ai_output(user_id, domain)
            if fresh_ai_output:
                return await self._build_completed_flow(user_id, domain, progress, fresh_ai_output)

        if task and task["status"] == "failed":
            # Previous attempt failed -> clear and retry
            await ai_task_manager.clear_task(user_id, domain)

        # No task running -> start AI in background, return processing immediately
        await ai_task_manager.set_processing(user_id, domain)

        # Launch background task (non-blocking) — keep reference to prevent GC
        _bg_task = asyncio.create_task(
            self._run_ai_in_background(user_id, domain)
        )
        _bg_task.add_done_callback(lambda t: t.exception() if not t.cancelled() else None)

        logger.info(f"AI background task started for {domain} (user {user_id}) -- returning processing status")
        return DomainFlowOut(
            status="processing",
            current=None,
            next=None,
            progress=progress,
            redirect="processing",
        )

    async def _get_fresh_completed_ai_output(self, user_id: int, domain: str) -> Optional[dict[str, Any]]:
        insight_result = await self.db.execute(
            select(Insight)
            .where(
                Insight.user_id == user_id,
                Insight.category == domain,
            )
            .order_by(Insight.updated_at.desc(), Insight.created_at.desc())
            .limit(1)
        )
        insight = insight_result.scalar_one_or_none()
        if not insight or not isinstance(insight.content, dict):
            return None

        answer_result = await self.db.execute(
            select(DomainAnswer)
            .where(
                DomainAnswer.user_id == user_id,
                DomainAnswer.domain == domain,
            )
            .order_by(DomainAnswer.updated_at.desc())
            .limit(1)
        )
        latest_answer = answer_result.scalar_one_or_none()
        if latest_answer and latest_answer.updated_at and latest_answer.updated_at > insight.updated_at:
            return None

        return insight.content

    async def _run_ai_in_background(self, user_id: int, domain: str) -> None:
        """Runs AI processing in background with its own DB session."""
        from app.core.database import AsyncSessionLocal
        try:
            async with AsyncSessionLocal() as db:
                service = DomainService(db)
                result = await service._process_ai_completion(user_id, domain)
                await ai_task_manager.set_completed(user_id, domain, result)
                logger.info(f"Background AI task completed for {domain} (user {user_id})")
        except Exception as e:
            await ai_task_manager.set_failed(user_id, domain, str(e))
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
                select(Image)
                .where(Image.user_id == user_id, Image.domain == domain)
                .order_by(Image.uploaded_at.desc())
            )
            return [{"view": img.view, "url": img.url or img.s3_key} for img in result.scalars().all()]
        except Exception as e:
            logger.warning(f"Could not fetch images for {domain} (user {user_id}): {e}")
            return []

    async def _fashion_required_scans_ready(self, user_id: int) -> tuple[bool, bool]:
        """Return whether latest fashion front/back scans exist for a user."""
        result = await self.db.execute(
            select(Image.view)
            .where(
                Image.user_id == user_id,
                Image.domain == "fashion",
                Image.view.in_(["front", "back"]),
            )
            .order_by(Image.uploaded_at.desc())
        )
        present_views = {str(view).lower() for (view,) in result.all() if view}
        return "front" in present_views, "back" in present_views

    async def _facial_required_scans_ready(self, user_id: int) -> tuple[bool, bool, bool]:
        """Return whether latest facial front/right/left scans exist for a user."""
        result = await self.db.execute(
            select(Image.view)
            .where(
                Image.user_id == user_id,
                Image.domain == "facial",
                Image.view.in_(["front", "right", "left"]),
            )
            .order_by(Image.uploaded_at.desc())
        )
        present_views = {str(view).lower() for (view,) in result.all() if view}
        return "front" in present_views, "right" in present_views, "left" in present_views

    def _extract_score(self, domain: str, ai_output: dict) -> Optional[float]:
        return extract_domain_score(domain, ai_output)

    async def _get_today_completion_record(self, user_id: int, domain: str) -> Optional[WorkoutCompletion]:
        result = await self.db.execute(
            select(WorkoutCompletion).where(
                WorkoutCompletion.user_id == user_id,
                WorkoutCompletion.domain == domain,
                WorkoutCompletion.date == date.today(),
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    def _normalize_quit_porn_checklist(items: list[Any], completed_indices: set[int]) -> list[dict[str, Any]]:
        normalized = []
        for idx, item in enumerate(items):
            title = item.get("title") if isinstance(item, dict) else str(item)
            description = item.get("description", "") if isinstance(item, dict) else ""
            duration = item.get("duration", "") if isinstance(item, dict) else ""
            normalized.append({
                "seq": idx + 1,
                "title": title or f"Checklist Item {idx + 1}",
                "subtitle": description,
                "description": description,
                "duration": duration,
                "completed": idx in completed_indices,
            })
        return normalized

    @staticmethod
    def _normalize_quit_porn_daily_tasks(
        items: list[Any],
        completed_indices: set[int],
        checklist_count: int,
    ) -> list[dict[str, Any]]:
        normalized = []
        for idx, item in enumerate(items):
            if isinstance(item, dict):
                title = item.get("title", "")
                description = item.get("description", "")
                duration = item.get("duration", "")
                existing_completed = bool(item.get("completed", False))
                seq = item.get("seq", idx + 1)
            else:
                title = str(item)
                description = ""
                duration = ""
                existing_completed = False
                seq = idx + 1

            normalized.append({
                "seq": seq,
                "title": title or f"Task {idx + 1}",
                "subtitle": description,
                "description": description,
                "duration": duration,
                "completed": (checklist_count + idx) in completed_indices or existing_completed,
            })
        return normalized

    @staticmethod
    def _extract_number(value: Any, default: float = 0.0) -> float:
        import re

        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            match = re.search(r"-?\d+(?:\.\d+)?", value.replace(",", ""))
            if match:
                try:
                    return float(match.group(0))
                except ValueError:
                    return default
        return default

    @classmethod
    def _extract_percent(cls, value: Any, default: float = 0.0) -> float:
        return max(0.0, min(100.0, cls._extract_number(value, default)))

    @classmethod
    def _extract_calorie_balance_percent(cls, value: Any) -> float:
        if not isinstance(value, str) or "/" not in value:
            return cls._extract_percent(value, 0.0)
        try:
            consumed_raw, target_raw = value.split("/", 1)
            consumed = cls._extract_number(consumed_raw.strip(), 0.0)
            target = cls._extract_number(target_raw.strip(), 0.0)
            if target <= 0:
                return 0.0
            return max(0.0, min(100.0, round((consumed / target) * 100, 1)))
        except Exception:
            return 0.0

    @staticmethod
    def _diet_icon_url(name: str) -> str:
        return f"https://api.lookslabai.com/static/icons/{name}.png"

    @staticmethod
    def _completed_index_set(completion_record: Optional[WorkoutCompletion]) -> set[int]:
        return set(completion_record.completed_indices or []) if completion_record else set()

    @staticmethod
    def _normalize_simple_completion_items(
        items: list[Any],
        completed_indices: set[int],
        start_offset: int = 0,
    ) -> list[dict[str, Any]]:
        normalized: list[dict[str, Any]] = []
        for idx, item in enumerate(items):
            if isinstance(item, dict):
                normalized_item = dict(item)
            else:
                normalized_item = {"title": str(item)}

            normalized_item.setdefault("seq", idx + 1)
            normalized_item["completed"] = (start_offset + idx) in completed_indices
            normalized.append(normalized_item)
        return normalized

    @staticmethod
    def _default_diet_morning_items() -> list[dict[str, Any]]:
        return [
            {
                "seq": 1,
                "title": "Breakfast",
                "subtitle": "Oatmeal with fruits & nuts",
                "description": "Balanced carbs + fiber for stable morning energy.",
                "duration": "10 min",
            },
            {
                "seq": 2,
                "title": "Morning Snack",
                "subtitle": "Yogurt or smoothie",
                "description": "Add protein to reduce cravings before lunch.",
                "duration": "5 min",
            },
            {
                "seq": 3,
                "title": "Hydration",
                "subtitle": "Drink 1 glass of water",
                "description": "Start hydration early to improve digestion and focus.",
                "duration": "1 min",
            },
        ]

    @staticmethod
    def _default_diet_evening_items() -> list[dict[str, Any]]:
        return [
            {
                "seq": 1,
                "title": "Lunch",
                "subtitle": "Balanced plate: protein + veggies + carbs",
                "description": "Keep portions steady and avoid sugary drinks.",
                "duration": "20 min",
            },
            {
                "seq": 2,
                "title": "Afternoon Snack",
                "subtitle": "Fruit or nuts",
                "description": "Use whole foods to avoid evening overeating.",
                "duration": "5 min",
            },
            {
                "seq": 3,
                "title": "Dinner",
                "subtitle": "Light, easy-to-digest meal",
                "description": "Prefer early dinner and lower heavy fats late night.",
                "duration": "20 min",
            },
        ]

    @staticmethod
    def _default_diet_today_focus() -> list[str]:
        return [
            "Build Muscle",
            "Maintenance",
            "Clean & Energetic Diet",
            "Fatloss",
        ]

    @staticmethod
    def _default_diet_nutrition_targets() -> dict[str, Any]:
        return {
            "daily_calories": 2000,
            "protein_g": 120,
            "carbs_g": 200,
            "fat_g": 65,
            "water_glasses": 8,
            "fiber_g": 25,
        }

    @staticmethod
    def _default_diet_recovery_checklist() -> list[str]:
        return [
            "Ate all planned meals",
            "Drank at least 8 glasses of water",
            "Included fruits & vegetables",
            "Took rest if needed",
        ]

    @classmethod
    def _normalize_diet_plan_items(
        cls,
        items: list[Any],
        completed_indices: set[int],
        start_offset: int,
    ) -> list[dict[str, Any]]:
        normalized: list[dict[str, Any]] = []
        for idx, item in enumerate(items):
            if isinstance(item, dict):
                title = item.get("title", "")
                description = item.get("description", "")
                subtitle = item.get("subtitle") or item.get("time") or ""
                duration = item.get("duration") or item.get("time") or ""
                seq = item.get("seq", idx + 1)
            else:
                title = str(item)
                description = ""
                subtitle = ""
                duration = ""
                seq = idx + 1

            normalized.append({
                "seq": seq,
                "title": title,
                "subtitle": subtitle,
                "description": description,
                "duration": duration,
                "completed": (start_offset + idx) in completed_indices,
            })
        return normalized

    async def _build_completed_flow(
        self,
        user_id: int,
        domain: str,
        progress: DomainProgressOut,
        ai_output: Optional[dict[str, Any]],
    ) -> DomainFlowOut:
        def _get(key: str) -> Optional[Any]:
            return ai_output.get(key) if ai_output else None

        if domain == "fashion":
            attributes = _get("attributes") or {}
            routine = _get("routine") or {}
            weekly_plan = routine.get("weekly_plan") if isinstance(routine, dict) else []
            seasonal_style = routine.get("seasonal_style") if isinstance(routine, dict) else {}
            images = await self._get_domain_images(user_id, domain)

            def _scan_url(view_name: str) -> Optional[str]:
                for image in images:
                    if str(image.get("view", "")).lower() == view_name:
                        return image.get("url")
                return None

            front_scan = _scan_url("front")
            back_scan = _scan_url("back")
            profile_traits = [
                {"key": "body_type", "label": "Body Type", "value": str(attributes.get("body_type") or "Athletic")},
                {"key": "undertone", "label": "Undertone", "value": str(attributes.get("undertone") or "Warm")},
                {"key": "style", "label": "Style", "value": str(attributes.get("style") or "Classic")},
            ]
            analyzing_insights = attributes.get("analyzing_insights") if isinstance(attributes.get("analyzing_insights"), list) else []
            if not analyzing_insights:
                analyzing_insights = [
                    "Balanced style profile generated",
                    "Recommendations aligned with your goals",
                ]

            return DomainFlowOut(
                status="completed",
                redirect="completed_flow",
                progress=progress,
                ai_message=str(_get("motivational_message") or "Own your style with confidence every day."),
                ai_attributes={
                    "body_type": profile_traits[0]["value"],
                    "undertone": profile_traits[1]["value"],
                    "style": profile_traits[2]["value"],
                },
                ai_summary={
                    "title": "Your Style Profile",
                    "subtitle": "AI analysis complete",
                    "profile_traits": profile_traits,
                    "review_scans": [
                        {"key": "front", "label": "Front View", "url": front_scan},
                        {"key": "back", "label": "Back View", "url": back_scan},
                    ],
                    "analyzing_insights": [str(item) for item in analyzing_insights[:5]],
                    "best_clothing_fits": [str(item) for item in (attributes.get("best_clothing_fits") or [])[:3]],
                    "styles_to_avoid": [str(item) for item in (attributes.get("styles_to_avoid") or [])[:3]],
                    "warm_palette": [str(item) for item in (attributes.get("warm_palette") or [])[:6]],
                },
                # Keep generic ai_routine for existing clients while adding UI-shaped cards below.
                ai_routine={
                    "weekly_plan": weekly_plan if isinstance(weekly_plan, list) else [],
                    "seasonal_style": seasonal_style if isinstance(seasonal_style, dict) else {},
                },
                daily_plan={
                    "title": "Weekly Plan",
                    "subtitle": "Daily style themes to keep you sharp",
                    "weekly_plan": weekly_plan if isinstance(weekly_plan, list) else [],
                    "season_tabs": ["summer", "monsoon", "winter"],
                    "default_season": "summer",
                    "seasonal_style": seasonal_style if isinstance(seasonal_style, dict) else {},
                },
            )

        if domain == "quit_porn":
            progress_tracking = _get("progress_tracking") or {}
            recovery_path = _get("recovery_path") or {}
            completion_record = await self._get_today_completion_record(user_id, domain)
            completed_indices = self._completed_index_set(completion_record)

            raw_checklist = progress_tracking.get("recovery_checklist") or [
                "Set your daily intention",
                "Evening reflection",
                "Productive alone time",
                "Connect with someone",
            ]
            checklist_items = self._normalize_quit_porn_checklist(raw_checklist, completed_indices)

            raw_daily_tasks = recovery_path.get("daily_tasks") or []
            daily_tasks = self._normalize_quit_porn_daily_tasks(raw_daily_tasks, completed_indices, len(checklist_items))
            streak = recovery_path.get("streak") or {
                "current_streak": 0,
                "longest_streak": 0,
                "next_goal": 7,
                "streak_message": "Today is day one. Let's make it count!",
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
                    "recovery_checklist": checklist_items,
                },
                ai_recovery={
                    "streak": streak,
                    "daily_tasks": daily_tasks,
                },
            )

        if domain == "diet":
            attributes = _get("attributes") or {}
            nutrition = _get("nutrition_targets") or {}
            routine = _get("routine") or {}
            progress_tracking = _get("progress_tracking") or {}
            completion_record = await self._get_today_completion_record(user_id, domain)
            completed_indices = self._completed_index_set(completion_record)

            today_focus = attributes.get("today_focus")
            if not isinstance(today_focus, list):
                today_focus = []
            if not today_focus:
                today_focus = self._default_diet_today_focus()

            if not isinstance(nutrition, dict):
                nutrition = {}
            if not nutrition:
                nutrition = self._default_diet_nutrition_targets()

            calories_value = str(attributes.get("calories_intake") or nutrition.get("daily_calories") or progress_tracking.get("daily_calories") or "0")
            calories_numeric = str(int(self._extract_number(calories_value, 0.0)))
            activity_level = str(attributes.get("activity") or attributes.get("activity_level") or "Moderate")
            posture_insight = str(attributes.get("posture_insight") or "Consistency improves energy, digestion & overall health over time. Keep going!")

            meals_summary = attributes.get("meals_summary") if isinstance(attributes.get("meals_summary"), dict) else {}
            total_meals = int(meals_summary.get("total_meals", 0) or 0)
            total_snacks = int(meals_summary.get("total_snacks", 0) or 0)
            prep_time_min = int(meals_summary.get("prep_time_min", 0) or 0)

            morning_items_raw = routine.get("morning") if isinstance(routine.get("morning"), list) else []
            evening_items_raw = routine.get("evening") if isinstance(routine.get("evening"), list) else []
            if not morning_items_raw:
                morning_items_raw = self._default_diet_morning_items()
            if not evening_items_raw:
                evening_items_raw = self._default_diet_evening_items()
            morning_items = self._normalize_diet_plan_items(morning_items_raw, completed_indices, 0)
            evening_items = self._normalize_diet_plan_items(evening_items_raw, completed_indices, len(morning_items))

            checklist_raw = progress_tracking.get("recovery_checklist")
            if not isinstance(checklist_raw, list):
                checklist_raw = []
            if not checklist_raw:
                checklist_raw = self._default_diet_recovery_checklist()
            checklist_items = []
            checklist_offset = len(morning_items) + len(evening_items)
            for idx, title in enumerate(checklist_raw[:4]):
                checklist_items.append({
                    "seq": idx + 1,
                    "title": str(title),
                    "completed": (checklist_offset + idx) in completed_indices,
                })

            diet_consistency_percent = self._extract_percent(progress_tracking.get("diet_consistency"), 0.0)
            calorie_balance_percent = self._extract_calorie_balance_percent(progress_tracking.get("calorie_balance"))

            return DomainFlowOut(
                status="completed",
                redirect="completed_flow",
                progress=progress,
                ai_message=str(_get("motivational_message") or "Small daily diet improvements create long-term healthy habits. You're doing great-keep up the momentum!"),
                ai_attributes={
                    "today_focus": [str(item) for item in today_focus[:4]],
                    "activity_level": activity_level,
                },
                ai_summary={
                    "subtitle": "Improve strength & track your workout progress",
                    "cards": [
                        {
                            "key": "calories",
                            "title": "Calories",
                            "value": calories_numeric,
                            "unit": "Intake",
                            "icon_url": self._diet_icon_url("calories"),
                        },
                        {
                            "key": "activity",
                            "title": "Activity",
                            "value": activity_level,
                            "unit": "",
                            "icon_url": self._diet_icon_url("activity"),
                        },
                    ],
                    "posture_insight": {
                        "title": "Posture Insight",
                        "text": posture_insight,
                    },
                    "today_meals": {
                        "title": "Today's Meals",
                        "subtitle": f"{total_meals} meals + {total_snacks} snacks • {prep_time_min} min prep",
                        "badge_icons": [
                            self._diet_icon_url("sun"),
                            self._diet_icon_url("moon"),
                        ],
                    },
                },
                daily_plan={
                    "insight_text": posture_insight,
                    "morning": morning_items,
                    "evening": evening_items,
                },
                progress_screen={
                    "subtitle": "Track your fitness journey",
                    "top_stats": [
                        {
                            "key": "daily_calorie",
                            "label": "Daily Calorie",
                            "value": str(progress_tracking.get("daily_calories") or calories_numeric),
                            "icon_url": self._diet_icon_url("calories"),
                        },
                        {
                            "key": "consistency",
                            "label": "Consistency",
                            "value": str(progress_tracking.get("consistency") or "0%"),
                            "icon_url": self._diet_icon_url("consistency"),
                        },
                        {
                            "key": "nutrition_balance",
                            "label": "Nutrition Balance",
                            "value": str(progress_tracking.get("nutrition_balance") or "0%"),
                            "icon_url": self._diet_icon_url("balance"),
                        },
                    ],
                    "mini_bars": [
                        {"title": "Diet Consistency", "percent": diet_consistency_percent},
                        {"title": "Calorie Balance", "percent": calorie_balance_percent},
                    ],
                    "main_consistency": {
                        "title": "Diet Consistency",
                        "subtitle": "Your diet tracking this week",
                        "percent": diet_consistency_percent,
                    },
                    "insight_text": str(_get("motivational_message") or "Small daily diet improvements create long-term healthy habits. You're doing great-keep up the momentum!"),
                    "daily_recovery_checklist": checklist_items,
                },
                ai_nutrition=nutrition if isinstance(nutrition, dict) else {},
            )

        if domain == "workout":
            attributes = _get("attributes") or {}
            exercises = _get("daily_exercises") or {}
            intensity = str(attributes.get("intensity", "Moderate")).lower()
            strength_map = {"low": "+5%", "moderate": "+12%", "high": "+20%"}
            strength_gain = strength_map.get(intensity, "+12%")
            progress_tracking = _get("progress_tracking") or {}
            completion_record = await self._get_today_completion_record(user_id, domain)
            completed_indices = self._completed_index_set(completion_record)
            morning_exercises = self._normalize_simple_completion_items(
                exercises.get("morning", []) if isinstance(exercises, dict) else [],
                completed_indices,
                0,
            )
            evening_exercises = self._normalize_simple_completion_items(
                exercises.get("evening", []) if isinstance(exercises, dict) else [],
                completed_indices,
                len(morning_exercises),
            )
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
                ai_exercises={
                    "morning": morning_exercises,
                    "evening": evening_exercises,
                },
            )

        if domain == "height":
            exercises = _get("daily_exercises") or {}
            completion_record = await self._get_today_completion_record(user_id, domain)
            completed_indices = self._completed_index_set(completion_record)
            morning_exercises = self._normalize_simple_completion_items(
                exercises.get("morning", []) if isinstance(exercises, dict) else [],
                completed_indices,
                0,
            )
            evening_exercises = self._normalize_simple_completion_items(
                exercises.get("evening", []) if isinstance(exercises, dict) else [],
                completed_indices,
                len(morning_exercises),
            )
            return DomainFlowOut(
                status="completed",
                current=None,
                next=None,
                progress=progress,
                redirect="completed_flow",
                ai_attributes=_get("attributes") or {},
                ai_message=_get("motivational_message"),
                ai_progress=_get("progress_tracking") or {},
                ai_today_focus=_get("today_focus") or [],
                ai_exercises={
                    "morning": morning_exercises,
                    "evening": evening_exercises,
                },
            )

        if domain in {"skincare", "haircare"}:
            routine = _get("routine") or {}
            completion_record = await self._get_today_completion_record(user_id, domain)
            completed_indices = self._completed_index_set(completion_record)
            today_items = self._normalize_simple_completion_items(
                routine.get("today", []) if isinstance(routine, dict) else [],
                completed_indices,
                0,
            )
            night_items = self._normalize_simple_completion_items(
                routine.get("night", []) if isinstance(routine, dict) else [],
                completed_indices,
                len(today_items),
            )
            return DomainFlowOut(
                status="completed",
                current=None,
                next=None,
                progress=progress,
                redirect="completed_flow",
                ai_attributes=_get("attributes") or {},
                ai_health=_get("health") or {},
                ai_concerns=_get("concerns") or {},
                ai_message=_get("motivational_message"),
                ai_remedies=_get("remedies") or {},
                ai_products=_get("products") or [],
                ai_routine={
                    "today": today_items,
                    "night": night_items,
                },
            )

        if domain == "facial":
            exercises = _get("daily_exercises") or {}
            exercise_items = exercises.get("exercises", []) if isinstance(exercises, dict) else []
            completion_record = await self._get_today_completion_record(user_id, domain)
            completed_indices = self._completed_index_set(completion_record)
            normalized_exercises = self._normalize_simple_completion_items(
                exercise_items,
                completed_indices,
                0,
            )
            feature_scores = _get("feature_scores") or {}
            features_list = feature_scores.get("features", []) if isinstance(feature_scores, dict) else []
            progress_tracking = _get("progress_tracking") or {}
            images = await self._get_domain_images(user_id, domain)

            def _scan_url(view_name: str) -> Optional[str]:
                for image in images:
                    if str(image.get("view", "")).lower() == view_name:
                        return image.get("url")
                return None

            def _feature_percent(name: str, default: int) -> int:
                for item in features_list:
                    if not isinstance(item, dict):
                        continue
                    item_name = str(item.get("name", "")).lower().replace(" ", "")
                    expected = name.lower().replace(" ", "")
                    if item_name == expected:
                        try:
                            return int(item.get("score", default))
                        except (TypeError, ValueError):
                            return default
                return default

            today_progress_done = sum(1 for item in normalized_exercises if item.get("completed"))
            checklist = progress_tracking.get("recovery_checklist", [])
            if not isinstance(checklist, list):
                checklist = []
            checklist_items = [
                {
                    "seq": idx + 1,
                    "title": str(item),
                    "completed": idx < today_progress_done,
                }
                for idx, item in enumerate(checklist[:3])
            ]

            return DomainFlowOut(
                status="completed",
                current=None,
                next=None,
                progress=progress,
                redirect="completed_flow",
                ai_attributes=_get("attributes") or {},
                ai_message=_get("motivational_message"),
                ai_features=feature_scores,
                ai_progress=progress_tracking,
                ai_exercises={
                    "total": len(normalized_exercises),
                    "exercises": normalized_exercises,
                },
                ai_summary={
                    "title": "Your Style Profile",
                    "subtitle": "Feature Scores",
                    "review_scans": [
                        {"key": "front", "label": "Front View", "url": _scan_url("front")},
                        {"key": "right", "label": "Right View", "url": _scan_url("right")},
                        {"key": "left", "label": "Left View", "url": _scan_url("left")},
                    ],
                    "overall_score": int(feature_scores.get("overall_score", 50)) if isinstance(feature_scores, dict) else 50,
                    "features": features_list if isinstance(features_list, list) else [],
                },
                daily_plan={
                    "title": "Personalized Exercise",
                    "subtitle": "Today's Progress",
                    "progress_done": today_progress_done,
                    "progress_total": len(normalized_exercises),
                    "exercises": normalized_exercises,
                },
                progress_screen={
                    "title": "Your Progress",
                    "subtitle": "Track your facial feature improvement journey",
                    "top_stats": [
                        {"key": "jawline", "label": "Jawline", "value": f"{_feature_percent('Jawline', 78)}%"},
                        {"key": "cheekbones", "label": "Cheekbones", "value": f"{_feature_percent('Cheek bones', 72)}%"},
                        {"key": "symmetry", "label": "Symmetry", "value": f"{int(progress_tracking.get('symmetry_score', 75))}%"},
                    ],
                    "consistency_percent": int(self._extract_percent(progress_tracking.get("consistency"), 85)),
                    "insight_text": str(_get("motivational_message") or "Small daily facial exercises create noticeable long-term improvements. Keep going!"),
                    "daily_recovery_checklist": checklist_items,
                },
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

    async def _process_ai_completion(self, user_id: int, domain: str) -> DomainFlowOut:
        progress = await self.calculate_progress(domain, user_id)
        answers_ctx = await self._get_answers_with_context(domain, user_id)
        images = await self._get_domain_images(user_id, domain)

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
                    img_result = await self.db.execute(
                        sa_select(Image).where(
                            Image.user_id == user_id,
                            Image.domain == domain,
                            Image.status == ImageStatus.processing,
                        )
                    )
                    processing_images = img_result.scalars().all()

                    # Build real bullet points from AI concerns output
                    concerns = ai_output.get("concerns", {})
                    points = []
                    if domain == "fashion":
                        attributes = ai_output.get("attributes", {})
                        raw_insights = attributes.get("analyzing_insights", []) if isinstance(attributes, dict) else []
                        if isinstance(raw_insights, list):
                            points = [str(item).strip() for item in raw_insights if str(item).strip()][:5]
                    elif isinstance(concerns, dict):
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

        return await self._build_completed_flow(user_id, domain, progress, ai_output)
    
    
