"""
Onboarding service layer.
Simplified - no complex flow logic.
"""

from uuid import UUID
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.models.onboarding import OnboardingSession, OnboardingQuestion, OnboardingAnswer
from app.schemas.onboarding import (
    OnboardingSessionOut,
    OnboardingAnswersResponse,
    OnboardingAnswerWithQuestion,
    WellnessMetricsOut
)


class OnboardingService:
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # -- Session Management -------------------------------------
    
    async def create_session(self, user_id: Optional[int] = None) -> OnboardingSession:
        """Create anonymous or user session."""
        session = OnboardingSession(
            user_id=user_id,
            is_paid=False,
            is_completed=False
        )
        
        self.db.add(session)
        await self.db.commit()
        
        self.db.expire(session)
        await self.db.refresh(session)
        
        logger.info(f"Created session: {session.id} for user: {user_id}")
        
        return session
    
    async def get_session(self, session_id: UUID) -> OnboardingSession:
        """Get session by ID."""
        session = await self.db.get(OnboardingSession, session_id)
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_id} not found"
            )
        
        return session
    
    # -- Answer Management --------------------------------------
    
    async def save_answer(
        self,
        session_id: UUID,
        question_id: int,
        answer: any
    ) -> OnboardingAnswer:
        """Save or update answer."""
        session = await self.get_session(session_id)
        
        question = await self.db.get(OnboardingQuestion, question_id)
        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Question {question_id} not found"
            )
        
        result = await self.db.execute(
            select(OnboardingAnswer).where(
                OnboardingAnswer.session_id == session_id,
                OnboardingAnswer.question_id == question_id
            )
        )
        existing_answer = result.scalar_one_or_none()
        
        if existing_answer:
            existing_answer.answer = answer
            await self.db.commit()
            self.db.expire(existing_answer)
            await self.db.refresh(existing_answer)
            logger.info(f"Updated answer for session {session_id}, question {question_id}")
            return existing_answer
        else:
            new_answer = OnboardingAnswer(
                session_id=session_id,
                question_id=question_id,
                answer=answer
            )
            self.db.add(new_answer)
            await self.db.commit()
            self.db.expire(new_answer)
            await self.db.refresh(new_answer)
            logger.info(f"Created answer for session {session_id}, question {question_id}")
            return new_answer
    
    # -- Domain & Payment ---------------------------------------
    
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
    
    # -- User Linking -------------------------------------------
    
    async def link_session_to_user(
        self,
        session_id: UUID,
        user_id: int
    ) -> OnboardingSession:
        """Link anonymous session to user and auto-populate profile fields."""
        session = await self.get_session(session_id)
        
        if session.user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Session already linked to a user"
            )
        
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
        rows = result.all()

        for answer, question in rows:
            q_lower = question.question.lower()
            if "name" in q_lower and not user.name:
                user.name = str(answer.answer)
            elif "age" in q_lower and not user.age:
                try:
                    if isinstance(answer.answer, dict) and "value" in answer.answer:
                        user.age = int(answer.answer["value"])
                    else:
                        user.age = int(str(answer.answer))
                except Exception:
                    logger.warning(f"Could not parse age answer: {answer.answer}")
            elif "gender" in q_lower and not user.gender:
                try:
                    if isinstance(answer.answer, list) and answer.answer:
                        user.gender = str(answer.answer[0])
                    else:
                        user.gender = str(answer.answer)
                except Exception:
                    logger.warning(f"Could not parse gender answer: {answer.answer}")

        await self.db.commit()
        await self.db.refresh(user, attribute_names=["subscription"])
        
        logger.info(f"Linked session {session_id} to user {user_id} and populated profile fields")
        return session
    
    # -- User Answers -------------------------------------------
    
    async def get_user_answers_with_questions(
        self,
        user_id: int
    ) -> OnboardingAnswersResponse:
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
        rows = result.all()
        
        answers_with_questions = [
            OnboardingAnswerWithQuestion(
                question_id=question.id,
                question=question.question,
                step=question.step,
                answer=answer.answer,
                answered_at=answer.created_at
            )
            for answer, question in rows
        ]
        
        logger.info(f"Returning {len(answers_with_questions)} answers for user {user_id}")
        return OnboardingAnswersResponse(user_id=user_id, answers=answers_with_questions)
    
    # -- Wellness Metrics ---------------------------------------
    
    async def get_wellness_metrics(self, user_id: int) -> WellnessMetricsOut:
        result = await self.db.execute(
            select(OnboardingSession)
            .where(OnboardingSession.user_id == user_id)
            .order_by(OnboardingSession.created_at.desc())
        )
        session = result.scalar_one_or_none()
        
        if not session:
            return WellnessMetricsOut(
                height=None,
                weight=None,
                sleep_hours=None,
                water_intake=None,
                daily_quote="Start your wellness journey today!"
            )
        
        result = await self.db.execute(
            select(OnboardingAnswer, OnboardingQuestion)
            .join(OnboardingQuestion, OnboardingAnswer.question_id == OnboardingQuestion.id)
            .where(OnboardingAnswer.session_id == session.id)
        )
        rows = result.all()
        
        metrics = {"height": None, "weight": None, "sleep_hours": None, "water_intake": None}
        
        for answer, question in rows:
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
            height=metrics["height"],
            weight=metrics["weight"],
            sleep_hours=metrics["sleep_hours"],
            water_intake=metrics["water_intake"],
            daily_quote="Keep pushing forward to achieve your goals!"
        )

