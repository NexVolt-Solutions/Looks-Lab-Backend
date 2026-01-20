from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.enums import DomainEnum
from app.schemas.domain import (
    DomainAnswerCreate,
    DomainFlowOut,
    DomainProgressOut,
    DomainSelectionResponse,
)
from app.utils.domain_utils import (
    select_domain_for_onboarding,
    save_domain_answer,
    get_domain_progress_for_user,
    next_or_complete_domain,
    domain_progress,
)
from app.utils.jwt_utils import get_current_user

router = APIRouter(tags=["Domain Flow"])


@router.patch("/onboarding/sessions/{session_id}/domain", response_model=DomainSelectionResponse)
def select_domain(
    session_id: int,
    domain: DomainEnum = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Select a domain during onboarding."""
    session = select_domain_for_onboarding(session_id, domain.value, db)
    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to select domain for this session")
    return DomainSelectionResponse(status="domain_selected", domain=session.selected_domain)


@router.get("/domains/{domain}/flow", response_model=DomainFlowOut)
def get_domain_flow(
    domain: DomainEnum,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return next unanswered question or completed flow with AI output."""
    return next_or_complete_domain(user_id=current_user.id, domain=domain.value, db=db)


@router.post("/domains/{domain}/answers", response_model=DomainFlowOut)
def submit_domain_answer(
    domain: DomainEnum,
    payload: DomainAnswerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Submit an answer and continue the flow."""
    payload.user_id = current_user.id
    save_domain_answer(domain.value, payload, db)
    return next_or_complete_domain(user_id=current_user.id, domain=domain.value, db=db)


@router.get("/domains/{domain}/progress", response_model=DomainProgressOut)
def get_domain_progress(
    domain: DomainEnum,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get progress for the current domain."""
    get_domain_progress_for_user(domain.value, current_user.id, db)
    return domain_progress(current_user.id, domain.value, db)

