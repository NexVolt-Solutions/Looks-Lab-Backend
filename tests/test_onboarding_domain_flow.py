import uuid
from datetime import datetime, timezone
from app.models.user import User
from app.models.onboarding import OnboardingSession, OnboardingQuestion, OnboardingAnswer
from app.models.domain import DomainQuestion, DomainAnswer
from app.utils.onboarding_utils import onboarding_progress
from app.utils.domain_utils import domain_progress


def test_domain_progress_complete(db):
    # Seed user
    random_email = f"pytest_{uuid.uuid4().hex[:6]}@example.com"
    user = User(email=random_email, name="Domain User", subscription_status="inactive")
    db.add(user)
    db.commit()
    db.refresh(user)

    # Seed domain questions
    questions = [
        DomainQuestion(domain="facial", question="Do you exercise daily?", type="choice", options=["Yes", "No"], seq=1),
        DomainQuestion(domain="facial", question="Do you sleep well?", type="choice", options=["Yes", "No"], seq=2),
    ]
    db.add_all(questions)
    db.commit()

    # Answer all questions
    for q in questions:
        answer = DomainAnswer(
            user_id=user.id,
            question_id=q.id,
            domain="facial",
            answer="Yes",
            created_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
        )
        db.add(answer)
    db.commit()

    # Assert progress is complete
    prog = domain_progress(user.id, "facial", db)
    assert prog["completed"] is True
    assert prog["progress_percent"] == 100.0


def test_onboarding_progress_partial(db):
    # Seed onboarding session
    session = OnboardingSession()
    db.add(session)
    db.commit()
    db.refresh(session)

    # Seed onboarding questions
    q1 = OnboardingQuestion(step="profile_setup", question="What is your age?", type="text", seq=1)
    q2 = OnboardingQuestion(step="daily_lifestyle", question="Do you smoke?", type="text", seq=2)
    db.add_all([q1, q2])
    db.commit()

    # Answer only one question
    answer = OnboardingAnswer(session_id=session.id, question_id=q1.id, answer="25", completed_at=datetime.now(timezone.utc))
    db.add(answer)
    db.commit()

    # Assert progress is partial
    prog = onboarding_progress(session.id, db)
    assert prog["overall"]["answered"] == 1
    assert prog["overall"]["total"] == 2
    assert prog["overall"]["completed"] is False


def test_onboarding_progress_complete(db):
    # Seed onboarding session
    session = OnboardingSession()
    db.add(session)
    db.commit()
    db.refresh(session)

    # Seed onboarding questions
    q1 = OnboardingQuestion(step="profile_setup", question="What is your age?", type="text", seq=1)
    q2 = OnboardingQuestion(step="daily_lifestyle", question="Do you smoke?", type="text", seq=2)
    db.add_all([q1, q2])
    db.commit()

    # Answer all questions
    for q in [q1, q2]:
        answer = OnboardingAnswer(session_id=session.id, question_id=q.id, answer="Sample", completed_at=datetime.now(timezone.utc))
        db.add(answer)
    db.commit()

    # Assert progress is complete
    prog = onboarding_progress(session.id, db)
    assert prog["overall"]["answered"] == 2
    assert prog["overall"]["completed"] is True

