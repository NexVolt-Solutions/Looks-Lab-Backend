import json
from sqlalchemy.orm import Session
from app.models.onboarding import OnboardingQuestion
from app.models.domain import DomainQuestion
from app.core.database import SessionLocal

ONBOARDING_STEPS = {"profile_setup", "daily_lifestyle", "motivation", "goals_focus", "experience_planning"}

def seed_questions():
    with open("app/static/questions.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    db: Session = SessionLocal()
    try:
        # Optional: Clear existing questions
        db.query(OnboardingQuestion).delete()
        db.query(DomainQuestion).delete()
        db.commit()
        print(" Old questions removed.")

        inserted = 0
        skipped = 0

        # Seed Onboarding Questions
        for step in ONBOARDING_STEPS:
            questions = data.get(step, [])
            for idx, q in enumerate(questions, start=1):
                if not q.get("question") or not q.get("type"):
                    skipped += 1
                    continue

                exists = db.query(OnboardingQuestion).filter_by(step=step, seq=idx).first()
                if exists:
                    skipped += 1
                    continue

                db.add(OnboardingQuestion(
                    step=step,
                    question=q["question"],
                    type=q["type"],
                    options=q.get("options"),
                    constraints=q.get("constraints"),
                    seq=idx
                ))
                inserted += 1

        # Seed Domain Questions
        for domain, questions in data.items():
            if domain in ONBOARDING_STEPS:
                continue

            for idx, q in enumerate(questions, start=1):
                if not q.get("question") or not q.get("type"):
                    skipped += 1
                    continue

                exists = db.query(DomainQuestion).filter_by(domain=domain, seq=idx).first()
                if exists:
                    skipped += 1
                    continue

                db.add(DomainQuestion(
                    domain=domain,
                    question=q["question"],
                    type=q["type"],
                    options=q.get("options"),
                    constraints=q.get("constraints"),
                    seq=idx
                ))
                inserted += 1

        db.commit()
        print(f" Seeding complete. Inserted: {inserted}, Skipped: {skipped}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_questions()

