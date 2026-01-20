from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.domain import DomainQuestion, DomainAnswer
from app.models.onboarding import OnboardingSession
from app.models.subscription import Subscription, SubscriptionStatus
from app.enums import DomainEnum

from app.schemas.domain import (
    DomainAnswerCreate,
    DomainFlowOut,
    DomainProgressOut,
    DomainQuestionOut,
)

from app.ai.hair_care.processor import analyze_haircare
from app.ai.skin_care.processor import analyze_skincare
from app.ai.hair_care.config import HaircareAIConfig
from app.ai.skin_care.config import SkincareAIConfig

from app.ai.fashion.processor import analyze_fashion
from app.ai.fashion.config import FashionAIConfig

from app.ai.workout.processor import analyze_workout
from app.ai.workout.config import WorkoutAIConfig

from app.ai.diet.processor import analyze_diet
from app.ai.diet.config import DietAIConfig

from app.ai.height.processor import analyze_height
from app.ai.height.config import HeightAIConfig

from app.ai.quit_porn.processor import analyze_quit_porn
from app.ai.quit_porn.config import QuitPornAIConfig

from app.ai.facial.processor import analyze_facial
from app.ai.facial.config import FacialAIConfig

haircare_config = HaircareAIConfig()
skincare_config = SkincareAIConfig()
fashion_config = FashionAIConfig()
workout_config = WorkoutAIConfig()
diet_config = DietAIConfig()
height_config = HeightAIConfig()
quit_porn_config = QuitPornAIConfig()
facial_config = FacialAIConfig()


# -------------------------------------------------
# Helpers
# -------------------------------------------------
def validate_domain(domain: str):
    """Validate domain against DomainEnum."""
    if domain not in DomainEnum.values():
        raise HTTPException(status_code=422, detail="Invalid domain selection")


def select_domain_for_onboarding(
    session_id: int, domain: str, db: Session
) -> OnboardingSession:
    validate_domain(domain)

    session = (
        db.query(OnboardingSession)
        .filter(OnboardingSession.id == session_id)
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Onboarding session not found")

    session.selected_domain = domain
    session.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(session)
    return session


def check_domain_entitlement(user_id: int, domain: str, db: Session):
    session = (
        db.query(OnboardingSession)
        .filter(OnboardingSession.user_id == user_id)
        .first()
    )
    if not session:
        raise HTTPException(status_code=403, detail="No onboarding session found")

    if session.selected_domain != domain:
        raise HTTPException(status_code=403, detail="Domain mismatch")

    if not session.is_paid:
        raise HTTPException(status_code=403, detail="Payment required")

    subscription = (
        db.query(Subscription)
        .filter(Subscription.user_id == user_id)
        .first()
    )
    if not subscription:
        raise HTTPException(status_code=403, detail="No subscription found")

    now = datetime.now(timezone.utc)
    if subscription.end_date and subscription.end_date < now:
        raise HTTPException(status_code=403, detail="Subscription expired")

    if subscription.status != SubscriptionStatus.active:
        raise HTTPException(
            status_code=403,
            detail=f"Subscription not active ({subscription.status})",
        )


# -------------------------------------------------
# Domain Questions & Answers
# -------------------------------------------------
def get_domain_questions(domain: str, db: Session):
    validate_domain(domain)

    questions = (
        db.query(DomainQuestion)
        .filter(DomainQuestion.domain == domain)
        .order_by(DomainQuestion.seq.asc())
        .all()
    )

    if not questions:
        raise HTTPException(
            status_code=404,
            detail=f"No questions found for domain '{domain}'",
        )
    return questions


def save_domain_answer(
    domain: str, payload: DomainAnswerCreate, db: Session
) -> DomainQuestionOut:
    validate_domain(domain)
    check_domain_entitlement(payload.user_id, domain, db)

    question = (
        db.query(DomainQuestion)
        .filter(DomainQuestion.id == payload.question_id)
        .first()
    )
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    now = datetime.now(timezone.utc)

    existing = (
        db.query(DomainAnswer)
        .filter(
            DomainAnswer.user_id == payload.user_id,
            DomainAnswer.question_id == payload.question_id,
        )
        .first()
    )

    if existing:
        existing.answer = payload.answer
        existing.completed_at = now
    else:
        db.add(
            DomainAnswer(
                user_id=payload.user_id,
                question_id=payload.question_id,
                domain=domain,
                answer=payload.answer,
                completed_at=now,
            )
        )

    db.commit()
    return DomainQuestionOut.model_validate(question)


def get_domain_answers_for_user(
    domain: str, user_id: int, db: Session
):
    validate_domain(domain)
    return (
        db.query(DomainAnswer)
        .filter(
            DomainAnswer.user_id == user_id,
            DomainAnswer.domain == domain,
        )
        .all()
    )


# -------------------------------------------------
# Progress
# -------------------------------------------------
def get_domain_progress_for_user(domain: str, user_id: int, db: Session) -> OnboardingSession:
    """
    Validate entitlement and return the onboarding session.
    Do not use this to fetch answers—use get_domain_answers_for_user instead.
    """
    validate_domain(domain)
    session = db.query(OnboardingSession).filter(OnboardingSession.user_id == user_id).first()
    if not session or not session.is_paid or session.selected_domain != domain:
        raise HTTPException(status_code=403, detail="No paid access for this domain")

    subscription = db.query(Subscription).filter(Subscription.user_id == user_id).first()
    if not subscription:
        raise HTTPException(status_code=403, detail="No subscription found for this user")

    now = datetime.now(timezone.utc)
    if subscription.end_date and subscription.end_date < now:
        raise HTTPException(status_code=403, detail="Subscription expired")
    if subscription.status != SubscriptionStatus.active:
        raise HTTPException(status_code=403, detail=f"Subscription not active (status={subscription.status})")

    return session


def domain_progress(
    user_id: int, domain: str, db: Session
) -> DomainProgressOut:
    questions = get_domain_questions(domain, db)

    answers = (
        db.query(DomainAnswer)
        .filter(
            DomainAnswer.user_id == user_id,
            DomainAnswer.domain == domain,
        )
        .all()
    )

    answered_ids = [a.question_id for a in answers]
    total = len(questions)
    answered = len(answered_ids)

    percent = (answered / total * 100) if total else 0.0

    subscription = (
        db.query(Subscription)
        .filter(Subscription.user_id == user_id)
        .first()
    )

    subscription_status = None
    if subscription:
        now = datetime.now(timezone.utc)
        if subscription.end_date and subscription.end_date < now:
            subscription_status = SubscriptionStatus.expired
        else:
            subscription_status = subscription.status

    return DomainProgressOut(
        user_id=user_id,
        domain=domain,
        progress={
            "total": total,
            "answered": answered,
            "completed": answered == total and total > 0,
        },
        answered_questions=answered_ids,
        total_questions=total,
        progress_percent=percent,
        subscription_status=subscription_status,
    )


# -------------------------------------------------
# MAIN FLOW (NEXT OR COMPLETE)
# -------------------------------------------------
def next_or_complete_domain(
    user_id: int, domain: str, db: Session
) -> DomainFlowOut:
    validate_domain(domain)
    check_domain_entitlement(user_id, domain, db)

    questions = get_domain_questions(domain, db)

    answered_ids = {
        qid
        for (qid,) in db.query(DomainAnswer.question_id)
        .filter(
            DomainAnswer.user_id == user_id,
            DomainAnswer.domain == domain,
        )
        .all()
    }
# -------------------------------
# Next unanswered question
# -------------------------------
    for idx, q in enumerate(questions):
        if q.id not in answered_ids:
            next_q = questions[idx + 1] if idx + 1 < len(questions) else None
            return DomainFlowOut(
                status="ok",
                current=DomainQuestionOut.model_validate(q),
                next=DomainQuestionOut.model_validate(next_q) if next_q else None,
                progress=domain_progress(user_id, domain, db),
                redirect=None,
            )


# -------------------------------
# Completed → AI processing
# -------------------------------
    progress = domain_progress(user_id, domain, db)
    answers = get_domain_answers_for_user(domain, user_id, db)

    question_map = {
        q.id: q.text
        for q in db.query(DomainQuestion)
        .filter(DomainQuestion.domain == domain)
        .all()
    }

    answers_ctx = [
        {
            "step": a.question_id,
            "question": question_map.get(a.question_id, ""),
            "answer": a.answer,
        }
        for a in answers
    ]

    images = []
    ai_out = None
    d = domain.lower()

    if d == "haircare" and len(answers_ctx) >= haircare_config.MIN_ANSWERS_REQUIRED:
        ai_out = analyze_haircare(answers_ctx, images)

    elif d == "skincare" and len(answers_ctx) >= skincare_config.MIN_ANSWERS_REQUIRED:
        if not skincare_config.REQUIRE_IMAGES or images:
            ai_out = analyze_skincare(answers_ctx, images)

    elif d == "fashion" and len(answers_ctx) >= fashion_config.MIN_ANSWERS_REQUIRED:
        ai_out = analyze_fashion(answers_ctx, images)

    elif d == "workout" and len(answers_ctx) >= workout_config.MIN_ANSWERS_REQUIRED:
        ai_out = analyze_workout(answers_ctx, images)

    elif d == "diet" and len(answers_ctx) >= diet_config.MIN_ANSWERS_REQUIRED:
        ai_out = analyze_diet(answers_ctx, images)

    elif d == "height" and len(answers_ctx) >= height_config.MIN_ANSWERS_REQUIRED:
        if not height_config.REQUIRE_IMAGES or images:
            ai_out = analyze_height(answers_ctx, images)

    elif d == "quit porn" and len(answers_ctx) >= quit_porn_config.MIN_ANSWERS_REQUIRED:
        ai_out = analyze_quit_porn(answers_ctx, images)

    elif d == "facial" and len(answers_ctx) >= facial_config.MIN_ANSWERS_REQUIRED:
        if not facial_config.REQUIRE_IMAGES or images:
            ai_out = analyze_facial(answers_ctx, images)

    return DomainFlowOut(
        status="completed",
        current=None,
        next=None,
        progress=progress,
        redirect="completed_flow",
        ai_attributes=ai_out.get("attributes") if ai_out else None,
        ai_health=ai_out.get("health") if ai_out else None,
        ai_concerns=ai_out.get("concerns") if ai_out else None,
        ai_routine=ai_out.get("routine") if ai_out else None,
        ai_remedies=ai_out.get("remedies") if ai_out else None,
        ai_products=ai_out.get("products") if ai_out else None,
        ai_recovery=ai_out.get("recovery_path") if ai_out else None,
        ai_progress=ai_out.get("progress_tracking") if ai_out else None,
        ai_message=ai_out.get("motivational_message") if ai_out else None,
        ai_features=ai_out.get("feature_scores") if ai_out else None,
        ai_exercises=ai_out.get("daily_exercises") if ai_out else None,
    )

