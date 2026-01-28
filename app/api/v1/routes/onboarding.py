"""
Onboarding routes.
Handles onboarding session flow and question progression.
"""
from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.models.user import User
from app.schemas.onboarding import (
    OnboardingAnswerCreate,
    OnboardingFlowOut,
    OnboardingSessionOut,
)
from app.services.onboarding_service import OnboardingService
from app.utils.jwt_utils import get_current_user

router = APIRouter()


@router.post("/sessions", response_model=OnboardingSessionOut)
async def create_onboarding_session(
        db: AsyncSession = Depends(get_async_db),
        current_user: User = Depends(get_current_user),
):
    onboarding_service = OnboardingService(db)
    session = await onboarding_service.create_session(user_id=current_user.id)
    return session


@router.get("/sessions/{session_id}/flow", response_model=OnboardingFlowOut)
async def get_onboarding_flow(
        session_id: UUID,
        step: str,
        index: int,
        db: AsyncSession = Depends(get_async_db),
        current_user: User = Depends(get_current_user),
):
    onboarding_service = OnboardingService(db)

    await onboarding_service.check_session_ownership(session_id, current_user.id)

    return await onboarding_service.next_or_complete(session_id, step)


@router.post("/sessions/{session_id}/answers", response_model=OnboardingFlowOut)
async def submit_onboarding_answer(
        session_id: UUID,
        payload: OnboardingAnswerCreate,
        db: AsyncSession = Depends(get_async_db),
        current_user: User = Depends(get_current_user),
):
    onboarding_service = OnboardingService(db)

    await onboarding_service.check_session_ownership(session_id, current_user.id)

    question = await onboarding_service.save_answer(session_id, payload)

    return await onboarding_service.next_or_complete(session_id, question.step)


@router.patch("/sessions/{session_id}/domain")
async def select_domain(
        session_id: UUID,
        domain: str,
        db: AsyncSession = Depends(get_async_db),
        current_user: User = Depends(get_current_user),
):
    onboarding_service = OnboardingService(db)

    await onboarding_service.check_session_ownership(session_id, current_user.id)

    session = await onboarding_service.select_domain(session_id, domain)

    return {
        "status": "domain_selected",
        "session_id": str(session.id),
        "domain": domain
    }


@router.patch("/sessions/{session_id}/payment")
async def confirm_payment(
        session_id: UUID,
        db: AsyncSession = Depends(get_async_db),
        current_user: User = Depends(get_current_user),
):
    onboarding_service = OnboardingService(db)

    await onboarding_service.check_session_ownership(session_id, current_user.id)

    session = await onboarding_service.confirm_payment(session_id)

    return {
        "status": "payment_confirmed",
        "session_id": str(session.id),
        "domain": session.selected_domain
    }


@router.patch("/sessions/{session_id}/link")
async def link_session_to_user_route(
        session_id: UUID,
        db: AsyncSession = Depends(get_async_db),
        current_user: User = Depends(get_current_user),
):
    onboarding_service = OnboardingService(db)

    session = await onboarding_service.link_session_to_user(session_id, current_user.id)

    return {
        "status": "linked",
        "user_id": current_user.id,
        "session_id": str(session.id)
    }


@router.get("/users/me/answers")
async def get_my_onboarding_answers(
        db: AsyncSession = Depends(get_async_db),
        current_user: User = Depends(get_current_user),
):
    onboarding_service = OnboardingService(db)
    answers = await onboarding_service.get_user_answers(current_user.id)

    return {
        "user_id": current_user.id,
        "answers": answers
    }

