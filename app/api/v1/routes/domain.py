"""
Domain routes.
Handles domain-specific questionnaire flows and AI processing.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.models.user import User
from app.schemas.domain import (
    DomainAnswerCreate,
    DomainFlowOut,
    DomainProgressOut,
    DomainQuestionOut
)
from app.services.domain_service import DomainService
from app.utils.jwt_utils import get_current_user

router = APIRouter()


@router.get("/{domain}/questions", response_model=list[DomainQuestionOut])
async def get_domain_questions(
        domain: str,
        db: AsyncSession = Depends(get_async_db),
        current_user: User = Depends(get_current_user),
):
    domain_service = DomainService(db)

    domain_service.validate_domain(domain)

    questions = await domain_service.get_domain_questions(domain)

    return questions


@router.get("/{domain}/flow", response_model=DomainFlowOut)
async def get_domain_flow(
        domain: str,
        db: AsyncSession = Depends(get_async_db),
        current_user: User = Depends(get_current_user),
):
    domain_service = DomainService(db)

    domain_service.validate_domain(domain)
    await domain_service.check_domain_access(current_user.id, domain)

    return await domain_service.next_or_complete(current_user.id, domain)


@router.post("/{domain}/answers", response_model=DomainFlowOut)
async def submit_domain_answer(
        domain: str,
        payload: DomainAnswerCreate,
        db: AsyncSession = Depends(get_async_db),
        current_user: User = Depends(get_current_user),
):
    domain_service = DomainService(db)

    payload.user_id = current_user.id

    domain_service.validate_domain(domain)
    await domain_service.check_domain_access(current_user.id, domain)

    await domain_service.save_answer(domain, payload)

    return await domain_service.next_or_complete(current_user.id, domain)


@router.get("/{domain}/progress", response_model=DomainProgressOut)
async def get_domain_progress(
        domain: str,
        db: AsyncSession = Depends(get_async_db),
        current_user: User = Depends(get_current_user),
):
    domain_service = DomainService(db)

    domain_service.validate_domain(domain)

    return await domain_service.calculate_progress(domain, current_user.id)


@router.get("/{domain}/answers")
async def get_domain_answers(
        domain: str,
        db: AsyncSession = Depends(get_async_db),
        current_user: User = Depends(get_current_user),
):
    domain_service = DomainService(db)

    domain_service.validate_domain(domain)

    answers = await domain_service.get_user_answers(domain, current_user.id)

    return {
        "user_id": current_user.id,
        "domain": domain,
        "answers": answers
    }


@router.post("/{domain}/retry-ai", response_model=DomainFlowOut)
async def retry_ai_processing(
        domain: str,
        db: AsyncSession = Depends(get_async_db),
        current_user: User = Depends(get_current_user),
):
    domain_service = DomainService(db)

    domain_service.validate_domain(domain)
    await domain_service.check_domain_access(current_user.id, domain)

    return await domain_service.next_or_complete(current_user.id, domain)


@router.get("/{domain}/access")
async def check_domain_access(
        domain: str,
        db: AsyncSession = Depends(get_async_db),
        current_user: User = Depends(get_current_user),
):
    domain_service = DomainService(db)

    try:
        domain_service.validate_domain(domain)

        await domain_service.check_domain_access(current_user.id, domain)

        return {
            "has_access": True,
            "domain": domain,
            "user_id": current_user.id,
            "message": "Access granted"
        }

    except Exception as e:
        return {
            "has_access": False,
            "domain": domain,
            "user_id": current_user.id,
            "message": str(e)
        }

