"""
Onboarding service layer.
Handles anonymous onboarding sessions, question flow, and user linking.
"""
from uuid import UUID, uuid4
from datetime import datetime, timezone

from fastapi import HTTPException
from fastapi import status as http_status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.utils.quotes import get_daily_quote

from app.core.logging import logger
from app.models.onboarding import OnboardingSession, OnboardingQuestion, OnboardingAnswer
from app.models.user import User
from app.schemas.onboarding import (
    OnboardingAnswerCreate,
    OnboardingFlowOut,
    OnboardingProgressOut,
    OnboardingQuestionOut
)

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

WELLNESS_KEYWORDS = {
    "height": ["height"],
    "weight": ["weight"],
    "sleep_hours": ["sleep"],
    "water_intake": ["water"],
}


class OnboardingService:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_session(self, user_id: int | None = None) -> OnboardingSession:
        """
        Create a new onboarding session.
        Can be anonymous (user_id=None) or linked to a user.
        """
        session = OnboardingSession(
            id=uuid4(),
            user_id=user_id,
            created_at=datetime.now(timezone.utc)
        )

        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)

        logger.info(
            f"Created onboarding session {session.id} for "
            f"{'user ' + str(user_id) if user_id else 'anonymous'}"
        )
        return session

    async def get_session(self, session_id: UUID) -> OnboardingSession:
        """Get onboarding session by ID."""
        result = await self.db.execute(
            select(OnboardingSession).where(OnboardingSession.id == session_id)
        )
        session = result.scalar_one_or_none()

        if not session:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Onboarding session not found"
            )

        return session

    async def link_session_to_user(self, session_id: UUID, user_id: int) -> OnboardingSession:
        """
        Link an anonymous onboarding session to a user account.
        Called after user signs in post-onboarding.

        Args:
            session_id: Onboarding session UUID
            user_id: User ID to link to

        Returns:
            Updated session

        Raises:
            HTTPException: If session not found or already linked
        """
        session = await self.get_session(session_id)

        if session.user_id is not None:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Session is already linked to a user account"
            )

        session.user_id = user_id
        session.updated_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(session)

        logger.info(f"Linked session {session_id} to user {user_id}")
        return session

    async def select_domain(self, session_id: UUID, domain: str) -> OnboardingSession:
        """Select a domain for the onboarding session."""
        if domain not in VALID_DOMAINS:
            raise HTTPException(
                status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
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
        """Confirm payment for the onboarding session."""
        session = await self.get_session(session_id)

        session.is_paid = True
        session.payment_confirmed_at = datetime.now(timezone.utc)
        session.updated_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(session)

        logger.info(f"Payment confirmed for session {session_id}")
        return session

    async def get_questions_for_step(self, step: str) -> list[OnboardingQuestion]:
        """Get all questions for a specific onboarding step."""
        result = await self.db.execute(
            select(OnboardingQuestion)
            .where(OnboardingQuestion.step == step)
            .order_by(OnboardingQuestion.seq.asc())
        )
        return list(result.scalars().all())

    async def save_answer(
        self,
        session_id: UUID,
        payload: OnboardingAnswerCreate
    ) -> OnboardingQuestion:
        """Save or update an answer to an onboarding question."""
        result = await self.db.execute(
            select(OnboardingQuestion).where(OnboardingQuestion.id == payload.question_id)
        )
        question = result.scalar_one_or_none()

        if not question:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
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
            logger.info(
                f"Updated answer for question {payload.question_id} "
                f"in session {session_id}"
            )
        else:
            answer = OnboardingAnswer(
                session_id=session_id,
                question_id=payload.question_id,
                answer=payload.answer,
                completed_at=datetime.now(timezone.utc),
            )
            self.db.add(answer)
            logger.info(
                f"Created answer for question {payload.question_id} "
                f"in session {session_id}"
            )

        await self.db.commit()
        return question

    async def get_user_answers_with_questions(self, user_id: int) -> dict:
        """
        Get user's onboarding answers with question context.

        Args:
            user_id: User ID

        Returns:
            Dict with user_id and list of answers with questions
        """
        # Get user's sessions
        result = await self.db.execute(
            select(OnboardingSession).where(OnboardingSession.user_id == user_id)
        )
        sessions = result.scalars().all()
        session_ids = [s.id for s in sessions]

        if not session_ids:
            return {"user_id": user_id, "answers": []}

        result = await self.db.execute(
            select(OnboardingAnswer, OnboardingQuestion)
            .join(
                OnboardingQuestion,
                OnboardingAnswer.question_id == OnboardingQuestion.id
            )
            .where(OnboardingAnswer.session_id.in_(session_ids))
            .order_by(OnboardingQuestion.seq.asc())
        )
        rows = result.all()

        answers = []
        for answer, question in rows:
            answers.append({
                "question_id": question.id,
                "question": question.question,
                "step": question.step,
                "answer": answer.answer,
                "answered_at": answer.completed_at
            })

        return {"user_id": user_id, "answers": answers}

    async def get_wellness_metrics(self, user_id: int) -> dict:
        """
        Extract wellness metrics from onboarding answers.
        Used for Home screen wellness overview section.

        Args:
            user_id: User ID

        Returns:
            Dict with height, weight, sleep_hours, water_intake, and daily_quote
        """
        # Get user's sessions
        result = await self.db.execute(
            select(OnboardingSession).where(OnboardingSession.user_id == user_id)
        )
        sessions = result.scalars().all()
        session_ids = [s.id for s in sessions]

        empty_metrics = {
            "height": None,
            "weight": None,
            "sleep_hours": None,
            "water_intake": None,
            "daily_quote": get_daily_quote(),
        }

        if not session_ids:
            return empty_metrics

        result = await self.db.execute(
            select(OnboardingAnswer, OnboardingQuestion)
            .join(
                OnboardingQuestion,
                OnboardingAnswer.question_id == OnboardingQuestion.id
            )
            .where(
                OnboardingAnswer.session_id.in_(session_ids),
                OnboardingQuestion.step.in_(["profile_setup", "daily_lifestyle"])
            )
            .order_by(OnboardingQuestion.seq.asc())
        )
        rows = result.all()

        wellness = empty_metrics.copy()

        for answer, question in rows:
            q_text = question.question.lower()

            for metric, keywords in WELLNESS_KEYWORDS.items():
                if any(keyword in q_text for keyword in keywords):
                    wellness[metric] = answer.answer
                    break

        # Daily quote is already set in empty_metrics and copied
        logger.info(f"Fetched wellness metrics for user {user_id}")
        return wellness

    async def calculate_progress(self, session_id: UUID) -> dict:
        """Calculate onboarding progress for a session."""
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
        """Get next question or complete onboarding."""
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
                    next=(
                        OnboardingQuestionOut.model_validate(next_questions[1])
                        if len(next_questions) > 1
                        else None
                    ),
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
        """Get the next step in onboarding order."""
        try:
            idx = ONBOARDING_ORDER.index(current_step)
            return (
                ONBOARDING_ORDER[idx + 1]
                if idx + 1 < len(ONBOARDING_ORDER)
                else None
            )
        except ValueError:
            return None

    async def _complete_onboarding(self, session_id: UUID) -> OnboardingFlowOut:
        """Mark onboarding as complete and determine next redirect."""
        session = await self.get_session(session_id)
        progress = await self.calculate_progress(session_id)

        # Only mark user as onboarded if session is linked
        if session.user_id:
            result = await self.db.execute(
                select(User).where(User.id == session.user_id)
            )
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
        """Determine where to redirect user after onboarding completion."""
        if not session.selected_domain:
            return "domain_selection"

        if session.selected_domain not in VALID_DOMAINS:
            return "invalid_domain"

        if not session.is_paid:
            return "payment_required"

        if not session.user_id:
            return "login_required"

        return "domain_flow"

