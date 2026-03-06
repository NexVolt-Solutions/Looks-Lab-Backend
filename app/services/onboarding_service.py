from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.models.onboarding import OnboardingAnswer, OnboardingQuestion, OnboardingSession
from app.utils.quotes import get_daily_quote
from app.schemas.onboarding import (
    OnboardingAnswersResponse,
    OnboardingAnswerWithQuestion,
    WellnessMetricsOut,
)


class OnboardingService:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_session(self, user_id: Optional[int] = None) -> OnboardingSession:
        session = OnboardingSession(user_id=user_id, is_paid=False, is_completed=False)
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        logger.info(f"Created session {session.id} for user {user_id}")
        return session

    async def get_session(self, session_id: UUID) -> OnboardingSession:
        session = await self.db.get(OnboardingSession, session_id)
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Session {session_id} not found")
        return session

    async def save_answer(self, session_id: UUID, question_id: int, answer: Any) -> OnboardingAnswer:
        await self.get_session(session_id)

        question = await self.db.get(OnboardingQuestion, question_id)
        if not question:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Question {question_id} not found")

        result = await self.db.execute(
            select(OnboardingAnswer).where(
                OnboardingAnswer.session_id == session_id,
                OnboardingAnswer.question_id == question_id
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            existing.answer = answer
            await self.db.commit()
            await self.db.refresh(existing)
            return existing

        new_answer = OnboardingAnswer(session_id=session_id, question_id=question_id, answer=answer)
        self.db.add(new_answer)
        await self.db.commit()
        await self.db.refresh(new_answer)
        return new_answer

    async def select_domain(self, session_id: UUID, domain: str) -> OnboardingSession:
        session = await self.get_session(session_id)
        session.selected_domain = domain
        await self.db.commit()
        logger.info(f"Session {session_id} selected domain: {domain}")
        return session

    async def confirm_payment(self, session_id: UUID) -> OnboardingSession:
        session = await self.get_session(session_id)
        session.is_paid = True
        session.payment_confirmed_at = datetime.now(timezone.utc)
        await self.db.commit()
        logger.info(f"Session {session_id} payment confirmed")
        return session

    async def link_session_to_user(self, session_id: UUID, user_id: int) -> OnboardingSession:
        session = await self.get_session(session_id)

        if session.user_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Session already linked to a user")

        session.user_id = user_id
        session.is_completed = True
        await self.db.commit()

        from app.models.user import User
        user = await self.db.get(User, user_id)

        result = await self.db.execute(
            select(OnboardingAnswer, OnboardingQuestion)
            .join(OnboardingQuestion, OnboardingAnswer.question_id == OnboardingQuestion.id)
            .where(OnboardingAnswer.session_id == session.id)
        )

        for answer, question in result.all():
            q_lower = question.question.lower()
            try:
                if "name" in q_lower and not user.name:
                    user.name = str(answer.answer)
                elif "age" in q_lower and not user.age:
                    val = answer.answer
                    user.age = int(val["value"] if isinstance(val, dict) and "value" in val else val)
                elif "gender" in q_lower and not user.gender:
                    val = answer.answer
                    user.gender = str(val[0] if isinstance(val, list) and val else val)
            except Exception:
                logger.warning(f"Could not parse '{q_lower}' answer: {answer.answer}")

        await self.db.commit()
        logger.info(f"Linked session {session_id} to user {user_id}")
        return session

    async def get_user_answers_with_questions(self, user_id: int) -> OnboardingAnswersResponse:
        result = await self.db.execute(
            select(OnboardingSession)
            .where(OnboardingSession.user_id == user_id)
            .order_by(OnboardingSession.created_at.desc())
        )
        session = result.scalar_one_or_none()

        if not session:
            return OnboardingAnswersResponse(user_id=user_id, answers=[])

        result = await self.db.execute(
            select(OnboardingAnswer, OnboardingQuestion)
            .join(OnboardingQuestion, OnboardingAnswer.question_id == OnboardingQuestion.id)
            .where(OnboardingAnswer.session_id == session.id)
            .order_by(OnboardingQuestion.id)
        )

        answers = [
            OnboardingAnswerWithQuestion(
                question_id=question.id,
                question=question.question,
                step=question.step,
                answer=answer.answer,
                answered_at=answer.created_at
            )
            for answer, question in result.all()
        ]

        return OnboardingAnswersResponse(user_id=user_id, answers=answers)

    _WELLNESS_ICONS = {
        "height":       "https://api.lookslabai.com/static/icons/WellnessHeight.png",
        "weight":       "https://api.lookslabai.com/static/icons/WellnessWeight.png",
        "sleep_hours":  "https://api.lookslabai.com/static/icons/WellnessSleep.png",
        "water_intake": "https://api.lookslabai.com/static/icons/WellnessWater.png",
    }

    async def get_wellness_metrics(self, user_id: int) -> WellnessMetricsOut:
        result = await self.db.execute(
            select(OnboardingSession)
            .where(OnboardingSession.user_id == user_id)
            .order_by(OnboardingSession.created_at.desc())
        )
        session = result.scalar_one_or_none()

        metrics: dict[str, Any] = {}
        if session:
            result = await self.db.execute(
                select(OnboardingAnswer, OnboardingQuestion)
                .join(OnboardingQuestion, OnboardingAnswer.question_id == OnboardingQuestion.id)
                .where(OnboardingAnswer.session_id == session.id)
            )
            for answer, question in result.all():
                q_lower = question.question.lower()
                if "height" in q_lower:
                    metrics["height"] = answer.answer
                elif "weight" in q_lower:
                    metrics["weight"] = answer.answer
                elif "sleep" in q_lower:
                    metrics["sleep_hours"] = answer.answer
                elif "water" in q_lower:
                    metrics["water_intake"] = answer.answer

        return WellnessMetricsOut(
            height={"value": metrics.get("height"), "icon_url": self._WELLNESS_ICONS["height"]},
            weight={"value": metrics.get("weight"), "icon_url": self._WELLNESS_ICONS["weight"]},
            sleep_hours={"value": metrics.get("sleep_hours"), "icon_url": self._WELLNESS_ICONS["sleep_hours"]},
            water_intake={"value": metrics.get("water_intake"), "icon_url": self._WELLNESS_ICONS["water_intake"]},
            daily_quote=get_daily_quote()
        )
        
        