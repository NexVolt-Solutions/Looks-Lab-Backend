from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.models.onboarding import OnboardingSession
from app.schemas.onboarding import (
    OnboardingAnswerCreate,
    OnboardingFlowOut,
    OnboardingSessionOut,
    OnboardingQuestionOut,
)
from app.utils.jwt_utils import get_current_user
from app.utils.onboarding_utils import (
    create_session,
    get_questions_for_step,
    save_answer,
    select_domain_for_session,
    confirm_payment_for_session,
    link_session_to_user,
    get_answers_for_user,
)
from app.utils.onboarding_utils import next_or_complete, onboarding_progress

router = APIRouter()


@router.post("/sessions", response_model=OnboardingSessionOut)
def create_onboarding_session(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new onboarding session for the authenticated user."""
    session = create_session(db)
    session = link_session_to_user(session.id, current_user.id, db)
    return session


@router.get("/sessions/{session_id}/flow", response_model=OnboardingFlowOut)
def get_onboarding_flow(
    session_id: UUID,
    step: str,
    index: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve the current onboarding question for a given session and step."""
    session = db.query(OnboardingSession).filter(OnboardingSession.id == session_id).first()
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this session")

    questions = get_questions_for_step(step, db)
    if index < 1 or index > len(questions):
        return next_or_complete(session_id, step, db)

    current_q = questions[index - 1]
    return OnboardingFlowOut(
        status="ok",
        current={
            "step": step,
            "index": index,
            "question": OnboardingQuestionOut.model_validate(current_q),
        },
        next={
            "step": step,
            "index": index + 1 if index + 1 <= len(questions) else None,
        },
        progress=onboarding_progress(session_id, db),
    )


@router.post("/sessions/{session_id}/answers", response_model=OnboardingFlowOut)
def submit_onboarding_answer(
    session_id: UUID,
    payload: OnboardingAnswerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Submit an answer for the current question in the onboarding flow."""
    session = db.query(OnboardingSession).filter(OnboardingSession.id == session_id).first()
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to submit answers for this session")

    question = save_answer(session_id, payload, db)
    return next_or_complete(session_id, question.step, db)


@router.patch("/sessions/{session_id}/domain")
def select_domain(
    session_id: UUID,
    domain: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Store the chosen domain against an onboarding session."""
    session = db.query(OnboardingSession).filter(OnboardingSession.id == session_id).first()
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to select domain for this session")

    session = select_domain_for_session(session_id, domain, db)
    return {"status": "domain_selected", "session_id": str(session.id), "domain": domain}


@router.patch("/sessions/{session_id}/payment")
def confirm_payment(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark the onboarding session as paid for the selected domain."""
    session = db.query(OnboardingSession).filter(OnboardingSession.id == session_id).first()
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to confirm payment for this session")

    session = confirm_payment_for_session(session_id, db)
    return {"status": "payment_confirmed", "session_id": str(session.id), "domain": session.selected_domain}


@router.patch("/sessions/{session_id}/link")
def link_session_to_user_route(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Attach an existing onboarding session to the authenticated user."""
    session = link_session_to_user(session_id, current_user.id, db)
    return {"status": "linked", "user_id": current_user.id, "session_id": str(session.id)}


@router.get("/users/me/answers")
def get_my_onboarding_answers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Fetch all onboarding answers for the authenticated user."""
    return get_answers_for_user(current_user.id, db)

