from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.schemas.domain import DomainAnswerCreate, DomainFlowOut
from app.utils.domain_utils import (
    select_domain_for_onboarding,
    save_domain_answer,
    get_domain_progress_for_user,
    next_or_complete_domain,
    domain_progress,
)
from app.utils.jwt_utils import get_current_user

router = APIRouter(tags=["Domain Flow"])


# -------------------------------------------------
# Select Domain during Onboarding
# -------------------------------------------------
@router.patch("/onboarding/sessions/{session_id}/domain")
def select_domain(
    session_id: int,
    domain: str = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = select_domain_for_onboarding(session_id, domain, db)

    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to select domain for this session",
        )

    return {
        "status": "domain_selected",
        "domain": session.selected_domain,
    }


# -------------------------------------------------
# Get Current Domain Flow (Next or Complete)
# -------------------------------------------------
@router.get("/domains/{domain}/flow", response_model=DomainFlowOut)
def get_domain_flow(
    domain: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns:
    - next unanswered question
    - OR completed flow with AI output
    """
    return next_or_complete_domain(
        user_id=current_user.id,
        domain=domain,
        db=db,
    )


# -------------------------------------------------
# Submit Answer & Continue Flow
# -------------------------------------------------
@router.post("/domains/{domain}/answers", response_model=DomainFlowOut)
def submit_domain_answer(
    domain: str,
    payload: DomainAnswerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    payload.user_id = current_user.id

    save_domain_answer(domain, payload, db)

    # After saving, always return next step or completion
    return next_or_complete_domain(
        user_id=current_user.id,
        domain=domain,
        db=db,
    )


# -------------------------------------------------
# Get Progress Only
# -------------------------------------------------
@router.get("/domains/{domain}/progress")
def get_domain_progress(
    domain: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # entitlement check (raises if invalid)
    get_domain_progress_for_user(domain, current_user.id, db)

    return {
        "status": "progress",
        "domain": domain,
        "progress": domain_progress(current_user.id, domain, db),
    }

