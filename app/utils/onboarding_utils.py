from uuid import UUID, uuid4
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.onboarding import OnboardingQuestion, OnboardingAnswer, OnboardingSession
from app.models.user import User
from app.schemas.onboarding import OnboardingQuestionOut, OnboardingFlowOut, OnboardingAnswerCreate

# ---------------------------
# Global Onboarding Section Order
# ---------------------------
ONBOARDING_ORDER = [
    "profile_setup",
    "daily_lifestyle",
    "motivation",
    "goals_focus",
    "experience_planning",
]

# ---------------------------
# Valid Domains (same as domain.py)
# ---------------------------
VALID_DOMAINS = {
    "skincare",
    "hair care",
    "fashion",
    "workout",
    "quit porn",
    "diet",
    "height",
    "facial",
}

# ---------------------------
# Session creation
# ---------------------------
def create_session(db: Session, user_id: int | None = None) -> OnboardingSession:
    session = OnboardingSession(id=uuid4(), user_id=user_id)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session

# ---------------------------
# Question helpers
# ---------------------------
def get_questions_for_step(step: str, db: Session) -> list[OnboardingQuestion]:
    return (
        db.query(OnboardingQuestion)
        .filter(OnboardingQuestion.step == step)
        .order_by(OnboardingQuestion.seq.asc())
        .all()
    )

def save_answer(session_id: UUID, payload: OnboardingAnswerCreate, db: Session) -> OnboardingQuestion:
    question = db.query(OnboardingQuestion).filter(OnboardingQuestion.id == payload.question_id).first()
    if not question:
        raise ValueError("Invalid question_id")

    answer = OnboardingAnswer(
        session_id=session_id,
        question_id=payload.question_id,
        answer=payload.answer,
        completed_at=datetime.now(timezone.utc),
    )
    db.add(answer)
    db.commit()
    db.refresh(answer)
    return question

# ---------------------------
# Domain & Payment helpers
# ---------------------------
def select_domain_for_session(session_id: UUID, domain: str, db: Session) -> OnboardingSession:
    session = db.query(OnboardingSession).filter(OnboardingSession.id == session_id).first()
    if not session:
        raise ValueError("Session not found")

    session.selected_domain = domain
    db.commit()
    db.refresh(session)
    return session

def confirm_payment_for_session(session_id: UUID, db: Session) -> OnboardingSession:
    session = db.query(OnboardingSession).filter(OnboardingSession.id == session_id).first()
    if not session:
        raise ValueError("Session not found")

    session.is_paid = True
    session.payment_confirmed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(session)
    return session

# ---------------------------
# Linking & Answers
# ---------------------------
def link_session_to_user(session_id: UUID, user_id: int, db: Session) -> OnboardingSession:
    session = db.query(OnboardingSession).filter(OnboardingSession.id == session_id).first()
    if not session:
        raise ValueError("Session not found")

    session.user_id = user_id
    db.commit()
    db.refresh(session)
    return session

def get_answers_for_user(user_id: int, db: Session) -> list[OnboardingAnswer]:
    sessions = db.query(OnboardingSession).filter(OnboardingSession.user_id == user_id).all()
    session_ids = [s.id for s in sessions]
    return db.query(OnboardingAnswer).filter(OnboardingAnswer.session_id.in_(session_ids)).all()

# ---------------------------
# Existing helpers
# ---------------------------
def validate_domain(domain: str):
    if domain not in VALID_DOMAINS:
        raise ValueError("Invalid domain selection")

def next_or_complete(session_id: UUID, step: str, db: Session) -> OnboardingFlowOut:
    questions = (
        db.query(OnboardingQuestion)
        .filter(OnboardingQuestion.step == step)
        .order_by(OnboardingQuestion.seq.asc())
        .all()
    )
    answered_ids = {
        qid for (qid,) in db.query(OnboardingAnswer.question_id)
        .filter(OnboardingAnswer.session_id == session_id).all()
    }

    for idx, q in enumerate(questions, start=1):
        if q.id not in answered_ids:
            return OnboardingFlowOut(
                status="ok",
                current={
                    "step": step,
                    "index": idx,
                    "question": OnboardingQuestionOut.model_validate(q),
                },
                next={
                    "step": step,
                    "index": idx + 1 if idx + 1 <= len(questions) else None,
                },
                progress=onboarding_progress(session_id, db),
            )

    next_step = next_section_key(step)
    if next_step:
        next_qs = (
            db.query(OnboardingQuestion)
            .filter(OnboardingQuestion.step == next_step)
            .order_by(OnboardingQuestion.seq.asc())
            .all()
        )
        if next_qs:
            first_q = next_qs[0]
            return OnboardingFlowOut(
                status="ok",
                current={
                    "step": next_step,
                    "index": 1,
                    "question": OnboardingQuestionOut.model_validate(first_q),
                },
                next={
                    "step": next_step,
                    "index": 2 if len(next_qs) > 1 else None,
                },
                progress=onboarding_progress(session_id, db),
            )

    session = db.query(OnboardingSession).filter(OnboardingSession.id == session_id).first()
    if session and session.user_id:
        user = db.query(User).filter(User.id == session.user_id).first()
        if user and not user.onboarding_complete:
            user.onboarding_complete = True
            db.commit()

    redirect = "domain_selection"
    if session:
        if not session.selected_domain:
            redirect = "domain_selection"
        elif session.selected_domain not in VALID_DOMAINS:
            redirect = "invalid_domain"
        elif not session.is_paid:
            redirect = "payment_required"
        elif not session.user_id:
            redirect = "login_required"
        else:
            redirect = "domain_flow"

    return OnboardingFlowOut(
        status="completed",
        current=None,
        next=None,
        progress=onboarding_progress(session_id, db),
        redirect=redirect,
    )

def next_section_key(current: str) -> str | None:
    try:
        i = ONBOARDING_ORDER.index(current)
        return ONBOARDING_ORDER[i + 1] if i + 1 < len(ONBOARDING_ORDER) else None
    except ValueError:
        return None

def onboarding_progress(session_id: UUID, db: Session) -> dict:
    all_qs = db.query(OnboardingQuestion).order_by(OnboardingQuestion.seq.asc()).all()
    answered_ids = {
        qid for (qid,) in db.query(OnboardingAnswer.question_id)
        .filter(OnboardingAnswer.session_id == session_id).all()
    }

    per_step = {}
    for s in ONBOARDING_ORDER:
        qs = [q for q in all_qs if q.step == s]
        total = len(qs)
        answered = sum(1 for q in qs if q.id in answered_ids)
        per_step[s] = {
            "total": total,
            "answered": answered,
            "completed": answered == total and total > 0,
        }

    overall_total = len(all_qs)
    overall_answered = len(answered_ids)

    return {
        "sections": per_step,
        "overall": {
            "total": overall_total,
            "answered": overall_answered,
            "completed": overall_answered == overall_total and overall_total > 0,
        },
    }

def check_domain_access(session: OnboardingSession) -> dict:
    if not session.selected_domain:
        return {"status": "denied", "reason": "domain_not_selected"}
    if session.selected_domain not in VALID_DOMAINS:
        return {"status": "denied", "reason": "invalid_domain"}
    if not session.is_paid:
        return {"status": "denied", "reason": "payment_required"}
    if not session.user_id:
        return {"status": "denied", "reason": "login_required"}
    return {"status": "granted", "domain": session.selected_domain}

