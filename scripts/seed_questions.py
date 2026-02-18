import json
from pathlib import Path
from sqlalchemy.orm import Session

from app.models.onboarding import OnboardingQuestion
from app.models.domain import DomainQuestion
from app.core.database import SyncSessionLocal


ONBOARDING_STEPS = {
    "profile_setup",
    "daily_lifestyle",
    "goals_focus",
    "motivation",
    "experience_planning",
}


def seed_questions():
    # Project root directory
    BASE_DIR = Path(__file__).resolve().parent.parent

    # Correct absolute path to JSON file
    json_path = BASE_DIR / "app" / "static" / "questions.json"

    if not json_path.exists():
        raise FileNotFoundError(f"questions.json not found at {json_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    db: Session = SyncSessionLocal()

    try:
        # Clear existing questions (dev safe)
        db.query(OnboardingQuestion).delete()
        db.query(DomainQuestion).delete()
        db.commit()

        print("Old questions removed.")

        inserted = 0
        skipped = 0

        # Seed Onboarding Questions
        for step in ONBOARDING_STEPS:
            questions = data.get(step, [])

            for idx, q in enumerate(questions, start=1):
                if not q.get("question") or not q.get("type"):
                    skipped += 1
                    continue

                db.add(
                    OnboardingQuestion(
                        step=step,
                        question=q["question"],
                        type=q["type"],
                        options=q.get("options"),
                        constraints=q.get("constraints"),
                        seq=idx,
                    )
                )
                inserted += 1

        # Seed Domain Questions
        for domain, questions in data.items():
            if domain in ONBOARDING_STEPS:
                continue

            for idx, q in enumerate(questions, start=1):
                if not q.get("question") or not q.get("type"):
                    skipped += 1
                    continue

                db.add(
                    DomainQuestion(
                        domain=domain,
                        question=q["question"],
                        type=q["type"],
                        options=q.get("options"),
                        constraints=q.get("constraints"),
                        seq=idx,
                    )
                )
                inserted += 1

        db.commit()
        print(f"Seeding complete. Inserted: {inserted}, Skipped: {skipped}")

    except Exception as e:
        db.rollback()
        print(f"Seeding failed: {e}")
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed_questions()
