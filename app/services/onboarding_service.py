"""
Onboarding service layer.
Handles onboarding session, question flow, and progression logic.
"""
from uuid import UUID, uuid4
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from app.models.onboarding import OnboardingSession, OnboardingQuestion, OnboardingAnswer
from app.models.user import User
from app.schemas.onboarding import (
    OnboardingAnswerCreate,
    OnboardingFlowOut,
    OnboardingProgressOut,
    OnboardingQuestionOut
)
from app.core.logging import logger

ONBOARDING_ORDER = [
    "profile_setup",
    "daily_lifestyle",
    "motivation",
    "goals_focus",
    "experience_planning",
]

VALID_DOMAINS = {
    "skincare",
    "haircare",
    "fashion",
    "workout",
    "quit porn",
    "diet",
    "height",
    "facial",
}


class OnboardingService:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_session(self, user_id: int | None = None) -> OnboardingSession:
        session = OnboardingSession(
            id=uuid4(),
            user_id=user_id,
            created_at=datetime.now(timezone.utc)
        )

        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)

        logger.info(f"Created onboarding session {session.id} for user {user_id or 'anonymous'}")
        return session

    async def get_session(self, session_id: UUID) -> OnboardingSession:
        result = await self.db.execute(
            select(OnboardingSession).where(OnboardingSession.id == session_id)
        )
        session = result.scalar_one_or_none()

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Onboarding session not found"
            )

        return session

    async def link_session_to_user(self, session_id: UUID, user_id: int) -> OnboardingSession:
        session = await self.get_session(session_id)

        session.user_id = user_id
        session.updated_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(session)

        logger.info(f"Linked session {session_id} to user {user_id}")
        return session

    async def select_domain(self, session_id: UUID, domain: str) -> OnboardingSession:
        if domain not in VALID_DOMAINS:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid domain. Must be one of: {', '.join(VALID_DOMAINS)}"
            )

        session = await self.get_session(session_id)

        session.selected_domain = domain
        session.updated_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(session)

        logger.info(f"Session {session_id} selected domain: {domain}")
        return session

    async def confirm_payment(self, session_id: UUID) -> OnboardingSession:
        session = await self.get_session(session_id)

        session.is_paid = True
        session.payment_confirmed_at = datetime.now(timezone.utc)
        session.updated_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(session)

        logger.info(f"Payment confirmed for session {session_id}")
        return session

    async def get_questions_for_step(self, step: str) -> list[OnboardingQuestion]:
        result = await self.db.execute(
            select(OnboardingQuestion)
            .where(OnboardingQuestion.step == step)
            .order_by(OnboardingQuestion.seq.asc())
        )
        return list(result.scalars().all())

    async def save_answer(self, session_id: UUID, payload: OnboardingAnswerCreate) -> OnboardingQuestion:
        result = await self.db.execute(
            select(OnboardingQuestion).where(OnboardingQuestion.id == payload.question_id)
        )
        question = result.scalar_one_or_none()

        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Question not found"
            )

        result = await self.db.execute(
            select(OnboardingAnswer).where(
                OnboardingAnswer.session_id == session_id,
                OnboardingAnswer.question_id == payload.question_id
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            existing.answer = payload.answer
            existing.updated_at = datetime.now(timezone.utc)
            logger.info(f"Updated answer for question {payload.question_id} in session {session_id}")
        else:
            answer = OnboardingAnswer(
                session_id=session_id,
                question_id=payload.question_id,
                answer=payload.answer,
                completed_at=datetime.now(timezone.utc),
            )
            self.db.add(answer)
            logger.info(f"Created answer for question {payload.question_id} in session {session_id}")

        await self.db.commit()
        return question

    async def get_user_answers(self, user_id: int) -> list[OnboardingAnswer]:
        result = await self.db.execute(
            select(OnboardingSession).where(OnboardingSession.user_id == user_id)
        )
        sessions = result.scalars().all()
        session_ids = [s.id for s in sessions]

        result = await self.db.execute(
            select(OnboardingAnswer).where(OnboardingAnswer.session_id.in_(session_ids))
        )
        return list(result.scalars().all())

    async def calculate_progress(self, session_id: UUID) -> dict:
        result = await self.db.execute(
            select(OnboardingQuestion).order_by(OnboardingQuestion.seq.asc())
        )
        all_questions = list(result.scalars().all())

        result = await self.db.execute(
            select(OnboardingAnswer.question_id)
            .where(OnboardingAnswer.session_id == session_id)
        )
        answered_ids = {qid for (qid,) in result.all()}

        per_step = {}
        for step in ONBOARDING_ORDER:
            step_questions = [q for q in all_questions if q.step == step]
            total = len(step_questions)
            answered = sum(1 for q in step_questions if q.id in answered_ids)

            per_step[step] = {
                "total": total,
                "answered": answered,
                "completed": answered == total and total > 0,
            }

        overall_total = len(all_questions)
        overall_answered = len(answered_ids)

        return {
            "sections": per_step,
            "overall": {
                "total": overall_total,
                "answered": overall_answered,
                "completed": overall_answered == overall_total and overall_total > 0,
            },
        }

    async def next_or_complete(self, session_id: UUID, step: str) -> OnboardingFlowOut:
        questions = await self.get_questions_for_step(step)

        result = await self.db.execute(
            select(OnboardingAnswer.question_id)
            .where(OnboardingAnswer.session_id == session_id)
        )
        answered_ids = {qid for (qid,) in result.all()}

        for idx, q in enumerate(questions, start=1):
            if q.id not in answered_ids:
                next_q = questions[idx] if idx < len(questions) else None
                progress = await self.calculate_progress(session_id)

                return OnboardingFlowOut(
                    status="ok",
                    current=OnboardingQuestionOut.model_validate(q),
                    next=OnboardingQuestionOut.model_validate(next_q) if next_q else None,
                    progress=OnboardingProgressOut(
                        session_id=session_id,
                        step=step,
                        answered_questions=list(answered_ids),
                        total_questions=len(questions),
                        progress=progress
                    ),
                    redirect=None
                )

        next_step = self._get_next_step(step)

        if next_step:
            next_questions = await self.get_questions_for_step(next_step)

            if next_questions:
                first_q = next_questions[0]
                progress = await self.calculate_progress(session_id)

                return OnboardingFlowOut(
                    status="ok",
                    current=OnboardingQuestionOut.model_validate(first_q),
                    next=OnboardingQuestionOut.model_validate(next_questions[1]) if len(next_questions) > 1 else None,
                    progress=OnboardingProgressOut(
                        session_id=session_id,
                        step=next_step,
                        answered_questions=list(answered_ids),
                        total_questions=len(next_questions),
                        progress=progress
                    ),
                    redirect=None
                )

        return await self._complete_onboarding(session_id)

    def _get_next_step(self, current_step: str) -> str | None:
        try:
            idx = ONBOARDING_ORDER.index(current_step)
            return ONBOARDING_ORDER[idx + 1] if idx + 1 < len(ONBOARDING_ORDER) else None
        except ValueError:
            return None

    async def _complete_onboarding(self, session_id: UUID) -> OnboardingFlowOut:
        session = await self.get_session(session_id)
        progress = await self.calculate_progress(session_id)

        if session.user_id:
            result = await self.db.execute(select(User).where(User.id == session.user_id))
            user = result.scalar_one_or_none()
            if user and not user.onboarding_complete:
                user.onboarding_complete = True
                await self.db.commit()
                logger.info(f"Marked onboarding complete for user {session.user_id}")

        redirect = self._determine_redirect(session)

        return OnboardingFlowOut(
            status="completed",
            current=None,
            next=None,
            progress=OnboardingProgressOut(
                session_id=session_id,
                step="completed",
                answered_questions=[],
                total_questions=0,
                progress=progress
            ),
            redirect=redirect
        )

    def _determine_redirect(self, session: OnboardingSession) -> str:
        if not session.selected_domain:
            return "domain_selection"

        if session.selected_domain not in VALID_DOMAINS:
            return "invalid_domain"

        if not session.is_paid:
            return "payment_required"

        if not session.user_id:
            return "login_required"

        return "domain_flow"

    async def check_session_ownership(self, session_id: UUID, user_id: int) -> None:
        session = await self.get_session(session_id)

        if session.user_id != user_id:
            logger.warning(f"User {user_id} attempted to access session {session_id} owned by {session.user_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this session"
            )

