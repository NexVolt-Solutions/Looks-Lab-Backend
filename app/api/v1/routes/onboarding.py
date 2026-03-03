"""
Onboarding routes.
Simplified - frontend handles flow.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.core.logging import logger
from app.core.rate_limit import RateLimits, limiter
from app.models.user import User
from app.models.onboarding import OnboardingQuestion
from app.schemas.onboarding import (
    OnboardingAnswerCreate,
    OnboardingSessionOut,
    OnboardingAnswersResponse,
    WellnessMetricsOut
)
from app.services.onboarding_service import OnboardingService
from app.utils.jwt_utils import get_current_user

router = APIRouter()


# ===========================================================
# Questions 
# ===========================================================

@router.get("/questions")
@limiter.limit(RateLimits.DEFAULT)
async def get_all_questions(
    request: Request,
    db: AsyncSession = Depends(get_async_db),
):
    """Get all onboarding questions."""
    result = await db.execute(
        select(OnboardingQuestion).order_by(OnboardingQuestion.id)
    )
    questions = result.scalars().all()
    
    logger.info(f"Returning {len(questions)} onboarding questions")
    
    return questions


# ===========================================================
# Anonymous Endpoints
# ===========================================================

@router.post("/sessions", response_model=OnboardingSessionOut)
@limiter.limit(RateLimits.DEFAULT)
async def create_onboarding_session(
    request: Request,
    db: AsyncSession = Depends(get_async_db),
):
    """Create anonymous session."""
    service = OnboardingService(db)
    return await service.create_session(user_id=None)


@router.post("/sessions/{session_id}/answers")
@limiter.limit(RateLimits.DEFAULT)
async def submit_onboarding_answer(
    request: Request,
    session_id: UUID,
    payload: OnboardingAnswerCreate,
    db: AsyncSession = Depends(get_async_db),
):
    """Save answer."""
    service = OnboardingService(db)
    
    await service.save_answer(
        session_id=session_id,
        question_id=payload.question_id,
        answer=payload.answer
    )
    
    return {"status": "answer_saved"}


@router.get("/sessions/{session_id}/answers")
@limiter.limit(RateLimits.DEFAULT)
async def get_session_answers(
    request: Request,
    session_id: UUID,
    db: AsyncSession = Depends(get_async_db)
):
    """Get all answers for a session."""
    service = OnboardingService(db)
    session = await service.get_session(session_id)
    
    # Get answers directly from DB
    from sqlalchemy import select
    from app.models.onboarding import OnboardingAnswer
    
    result = await db.execute(
        select(OnboardingAnswer)
        .where(OnboardingAnswer.session_id == session_id)
        .order_by(OnboardingAnswer.question_id)
    )
    answers = result.scalars().all()
    
    logger.info(f"Returning {len(answers)} answers for session {session_id}")
    
    return answers


# ===========================================================
# Domain APIs
# ===========================================================

@router.get("/domains")
@limiter.limit(RateLimits.DEFAULT)
async def get_available_domains(
    request: Request,
):
    """Domain list for frontend dropdown."""
    return {
        "domains": [
            "skincare",
            "haircare",
            "fashion",
            "workout",
            "quit porn",
            "diet",
            "height",
            "facial",
        ]
    }


@router.post("/sessions/{session_id}/domain")
@limiter.limit(RateLimits.DEFAULT)
async def select_domain(
    request: Request,
    session_id: UUID,
    domain: str = Query(...),
    db: AsyncSession = Depends(get_async_db),
):
    """Domain selection."""
    service = OnboardingService(db)
    session = await service.select_domain(session_id, domain)
    
    return {
        "status": "domain_selected",
        "session_id": str(session.id),
        "domain": session.selected_domain
    }


# ===========================================================
# Payment Confirmation
# ===========================================================

@router.post("/sessions/{session_id}/payment")
@limiter.limit(RateLimits.DEFAULT)
async def confirm_payment(
    request: Request,
    session_id: UUID,
    db: AsyncSession = Depends(get_async_db),
):
    """Confirm payment."""
    service = OnboardingService(db)
    session = await service.confirm_payment(session_id)
    
    return {
        "status": "payment_confirmed",
        "session_id": str(session.id),
        "domain": session.selected_domain
    }


# ===========================================================
# Authenticated Endpoints
# ===========================================================

@router.patch("/sessions/{session_id}/link")
@limiter.limit(RateLimits.DEFAULT)
async def link_session_to_user_route(
    request: Request,
    session_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    """Link session to user."""
    service = OnboardingService(db)
    session = await service.link_session_to_user(
        session_id=session_id,
        user_id=current_user.id
    )
    
    return {
        "status": "linked",
        "user_id": current_user.id,
        "session_id": str(session.id),
        "domain": session.selected_domain
    }


@router.get("/users/me/answers", response_model=OnboardingAnswersResponse)
@limiter.limit(RateLimits.DEFAULT)
async def get_my_onboarding_answers(
    request: Request,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    """Get user's answers with questions."""
    service = OnboardingService(db)
    return await service.get_user_answers_with_questions(current_user.id)


@router.get("/users/me/wellness", response_model=WellnessMetricsOut)
@limiter.limit(RateLimits.DEFAULT)
async def get_wellness_metrics(
    request: Request,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    """Get wellness metrics."""
    service = OnboardingService(db)
    return await service.get_wellness_metrics(current_user.id)
    
    