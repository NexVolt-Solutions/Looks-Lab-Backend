"""
Onboarding routes.
Handles anonymous onboarding flow that links to user after sign-in.
"""
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.core.rate_limit import RateLimits, limiter
from app.models.user import User
from app.schemas.onboarding import (
    OnboardingAnswerCreate,
    OnboardingFlowOut,
    OnboardingSessionOut,
    OnboardingAnswersResponse,
    WellnessMetricsOut
)
from app.services.onboarding_service import OnboardingService
from app.utils.jwt_utils import get_current_user

router = APIRouter()


# ── Anonymous Endpoints (No Auth Required) ───────────────────────

@router.post("/sessions", response_model=OnboardingSessionOut)
@limiter.limit(RateLimits.DEFAULT)
async def create_onboarding_session(
    request: Request,  # noqa: ARG001
    db: AsyncSession = Depends(get_async_db),
):
    """
    Create a new anonymous onboarding session.
    No authentication required - session can be linked to user later.
    """
    service = OnboardingService(db)
    return await service.create_session(user_id=None)


@router.get("/sessions/{session_id}/flow", response_model=OnboardingFlowOut)
@limiter.limit(RateLimits.DEFAULT)
async def get_onboarding_flow(
    session_id: UUID,
    step: str,
    index: int,
    request: Request,  # noqa: ARG001
    db: AsyncSession = Depends(get_async_db),
):
    """Get current onboarding flow state (anonymous - no auth required)."""
    service = OnboardingService(db)
    return await service.next_or_complete(session_id, step)


@router.post("/sessions/{session_id}/answers", response_model=OnboardingFlowOut)
@limiter.limit(RateLimits.DEFAULT)
async def submit_onboarding_answer(
    session_id: UUID,
    payload: OnboardingAnswerCreate,
    request: Request,  # noqa: ARG001
    db: AsyncSession = Depends(get_async_db),
):
    """Submit an answer to an onboarding question (anonymous)."""
    service = OnboardingService(db)
    question = await service.save_answer(session_id, payload)
    return await service.next_or_complete(session_id, question.step)


@router.patch("/sessions/{session_id}/domain")
@limiter.limit(RateLimits.DEFAULT)
async def select_domain(
    session_id: UUID,
    domain: str,
    request: Request,  # noqa: ARG001
    db: AsyncSession = Depends(get_async_db),
):
    """Select a domain for the onboarding session (anonymous)."""
    service = OnboardingService(db)
    session = await service.select_domain(session_id, domain)

    return {
        "status": "domain_selected",
        "session_id": str(session.id),
        "domain": domain
    }


@router.patch("/sessions/{session_id}/payment")
@limiter.limit(RateLimits.DEFAULT)
async def confirm_payment(
    session_id: UUID,
    request: Request,  # noqa: ARG001
    db: AsyncSession = Depends(get_async_db),
):
    """Confirm payment for the onboarding session (anonymous)."""
    service = OnboardingService(db)
    session = await service.confirm_payment(session_id)

    return {
        "status": "payment_confirmed",
        "session_id": str(session.id),
        "domain": session.selected_domain
    }


# ── Authenticated Endpoints (Auth Required) ───────────────────────

@router.patch("/sessions/{session_id}/link")
@limiter.limit(RateLimits.DEFAULT)
async def link_session_to_user_route(
    session_id: UUID,
    request: Request,  # noqa: ARG001
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    """
    Link an anonymous onboarding session to the authenticated user.
    Called after user signs in (post-onboarding).
    """
    service = OnboardingService(db)
    session = await service.link_session_to_user(session_id, current_user.id)

    return {
        "status": "linked",
        "user_id": current_user.id,
        "session_id": str(session.id),
        "domain": session.selected_domain
    }


@router.get("/users/me/answers", response_model=OnboardingAnswersResponse)
@limiter.limit(RateLimits.DEFAULT)
async def get_my_onboarding_answers(
    request: Request,  # noqa: ARG001
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get current user's onboarding answers with question context.
    Returns all answers mapped to their questions for reference.
    """
    service = OnboardingService(db)
    return await service.get_user_answers_with_questions(current_user.id)


@router.get("/users/me/wellness", response_model=WellnessMetricsOut)
@limiter.limit(RateLimits.DEFAULT)
async def get_wellness_metrics(
    request: Request,  # noqa: ARG001
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get user's wellness metrics for Home screen overview.

    Extracts from onboarding answers:
    - Height (from profile_setup step)
    - Weight (from profile_setup step)
    - Sleep Hours (from daily_lifestyle step)
    - Water Intake (from daily_lifestyle step)

    Returns:
        Wellness metrics for Home screen display cards
    """
    service = OnboardingService(db)
    return await service.get_wellness_metrics(current_user.id)

