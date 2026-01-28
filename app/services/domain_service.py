"""
Domain service layer.
Handles domain-specific questionnaire flows and AI processing.
"""
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from app.models.domain import DomainQuestion, DomainAnswer
from app.models.subscription import Subscription, SubscriptionStatus
from app.models.onboarding import OnboardingSession
from app.schemas.domain import (
    DomainAnswerCreate,
    DomainFlowOut,
    DomainProgressOut,
    DomainQuestionOut
)
from app.enums import DomainEnum
from app.core.logging import logger

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

ai_configs = {
    "skincare": SkincareAIConfig(),
    "haircare": HaircareAIConfig(),
    "facial": FacialAIConfig(),
    "diet": DietAIConfig(),
    "height": HeightAIConfig(),
    "workout": WorkoutAIConfig(),
    "quit porn": QuitPornAIConfig(),
    "fashion": FashionAIConfig(),
}

ai_processors = {
    "skincare": analyze_skincare,
    "haircare": analyze_haircare,
    "facial": analyze_facial,
    "diet": analyze_diet,
    "height": analyze_height,
    "workout": analyze_workout,
    "quit porn": analyze_quit_porn,
    "fashion": analyze_fashion,
}


class DomainService:

    def __init__(self, db: AsyncSession):
        self.db = db

    def validate_domain(self, domain: str) -> None:
        if domain not in DomainEnum.values():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid domain. Must be one of: {', '.join(DomainEnum.values())}"
            )

    async def check_domain_access(self, user_id: int, domain: str) -> None:
        result = await self.db.execute(
            select(OnboardingSession).where(OnboardingSession.user_id == user_id)
        )
        session = result.scalar_one_or_none()

        if not session:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No onboarding session found"
            )

        if session.selected_domain != domain:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Your selected domain is '{session.selected_domain}'"
            )

        if not session.is_paid:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="Payment required for domain access"
            )

        result = await self.db.execute(
            select(Subscription).where(Subscription.user_id == user_id)
        )
        subscription = result.scalar_one_or_none()

        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No active subscription found"
            )

        now = datetime.now(timezone.utc)

        if subscription.end_date and subscription.end_date < now:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="Subscription expired"
            )

        if subscription.status != SubscriptionStatus.active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Subscription not active (status: {subscription.status})"
            )

    async def get_domain_questions(self, domain: str) -> list[DomainQuestion]:
        self.validate_domain(domain)

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
        self.validate_domain(domain)
        await self.check_domain_access(payload.user_id, domain)

        result = await self.db.execute(
            select(DomainQuestion).where(DomainQuestion.id == payload.question_id)
        )
        question = result.scalar_one_or_none()

        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Question not found"
            )

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
            existing.updated_at = now
            logger.info(f"Updated answer for question {payload.question_id} (user {payload.user_id})")
        else:
            answer = DomainAnswer(
                user_id=payload.user_id,
                question_id=payload.question_id,
                domain=domain,
                answer=payload.answer,
                completed_at=now
            )
            self.db.add(answer)
            logger.info(f"Created answer for question {payload.question_id} (user {payload.user_id})")

        await self.db.commit()
        return question

    async def get_user_answers(self, domain: str, user_id: int) -> list[DomainAnswer]:
        self.validate_domain(domain)

        result = await self.db.execute(
            select(DomainAnswer).where(
                DomainAnswer.user_id == user_id,
                DomainAnswer.domain == domain
            )
        )
        return list(result.scalars().all())

    async def calculate_progress(self, domain: str, user_id: int) -> DomainProgressOut:
        questions = await self.get_domain_questions(domain)
        answers = await self.get_user_answers(domain, user_id)

        answered_ids = [a.question_id for a in answers]
        total = len(questions)
        answered = len(answered_ids)

        progress_percent = (answered / total * 100) if total else 0.0

        result = await self.db.execute(
            select(Subscription).where(Subscription.user_id == user_id)
        )
        subscription = result.scalar_one_or_none()

        subscription_status = None
        if subscription:
            now = datetime.now(timezone.utc)
            if subscription.end_date and subscription.end_date < now:
                subscription_status = SubscriptionStatus.expired
            else:
                subscription_status = subscription.status

        return DomainProgressOut(
            user_id=user_id,
            domain=domain,
            progress={
                "total": total,
                "answered": answered,
                "completed": answered == total and total > 0
            },
            answered_questions=answered_ids,
            total_questions=total,
            progress_percent=progress_percent,
            subscription_status=subscription_status
        )

    async def next_or_complete(self, user_id: int, domain: str) -> DomainFlowOut:
        self.validate_domain(domain)
        await self.check_domain_access(user_id, domain)

        questions = await self.get_domain_questions(domain)

        result = await self.db.execute(
            select(DomainAnswer.question_id).where(
                DomainAnswer.user_id == user_id,
                DomainAnswer.domain == domain
            )
        )
        answered_ids = {qid for (qid,) in result.all()}

        for idx, q in enumerate(questions):
            if q.id not in answered_ids:
                next_q = questions[idx + 1] if idx + 1 < len(questions) else None

                return DomainFlowOut(
                    status="ok",
                    current=DomainQuestionOut.model_validate(q),
                    next=DomainQuestionOut.model_validate(next_q) if next_q else None,
                    progress=await self.calculate_progress(domain, user_id),
                    redirect=None
                )

        return await self._process_ai_completion(user_id, domain)

    async def _process_ai_completion(self, user_id: int, domain: str) -> DomainFlowOut:
        progress = await self.calculate_progress(domain, user_id)
        answers = await self.get_user_answers(domain, user_id)

        result = await self.db.execute(
            select(DomainQuestion).where(DomainQuestion.domain == domain)
        )
        questions = result.scalars().all()
        question_map = {q.id: q.question for q in questions}

        answers_ctx = [
            {
                "step": a.question_id,
                "question": question_map.get(a.question_id, ""),
                "answer": a.answer
            }
            for a in answers
        ]

        images = []

        config = ai_configs.get(domain)
        processor = ai_processors.get(domain)

        ai_output = None

        if config and processor and len(answers_ctx) >= config.MIN_ANSWERS_REQUIRED:
            if config.REQUIRE_IMAGES and not images:
                logger.warning(f"Domain {domain} requires images but none provided for user {user_id}")
            else:
                try:
                    ai_output = processor(answers_ctx, images)
                    logger.info(f"AI processing complete for {domain} (user {user_id})")
                except Exception as e:
                    logger.error(f"AI processing failed for {domain} (user {user_id}): {e}")

        return DomainFlowOut(
            status="completed",
            current=None,
            next=None,
            progress=progress,
            redirect="completed_flow",
            ai_attributes=ai_output.get("attributes") if ai_output else None,
            ai_health=ai_output.get("health") if ai_output else None,
            ai_concerns=ai_output.get("concerns") if ai_output else None,
            ai_routine=ai_output.get("routine") if ai_output else None,
            ai_remedies=ai_output.get("remedies") if ai_output else None,
            ai_products=ai_output.get("products") if ai_output else None,
            ai_recovery=ai_output.get("recovery_path") if ai_output else None,
            ai_progress=ai_output.get("progress_tracking") if ai_output else None,
            ai_message=ai_output.get("motivational_message") if ai_output else None,
            ai_features=ai_output.get("feature_scores") if ai_output else None,
            ai_exercises=ai_output.get("daily_exercises") if ai_output else None
        )

