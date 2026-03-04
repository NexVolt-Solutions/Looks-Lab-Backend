import asyncio
import json
from pathlib import Path

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.core.logging import logger
from app.models.onboarding import OnboardingQuestion

BASE_DIR = Path(__file__).resolve().parent.parent
JSON_PATH = BASE_DIR / "app" / "data" / "onboarding_questions.json"


async def seed_questions() -> None:
    if not JSON_PATH.exists():
        logger.error(f"Questions file not found: {JSON_PATH}")
        print(f"Questions file not found at: {JSON_PATH}")
        return

    with open(JSON_PATH, encoding="utf-8") as f:
        data = json.load(f)

    questions_data = data.get("questions", [])
    if not questions_data:
        logger.error("No questions found in JSON file")
        print("No questions found in JSON file")
        return

    print(f"Found {len(questions_data)} questions to seed")

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(OnboardingQuestion))
        existing = result.scalars().all()

        if existing:
            print(f"Database already has {len(existing)} questions")
            if input("Delete and re-seed? (yes/no): ").lower() != "yes":
                print("Seeding cancelled")
                return

            for q in existing:
                await session.delete(q)
            await session.commit()
            print("Deleted existing questions")

        for q_data in questions_data:
            session.add(OnboardingQuestion(
                step=q_data["step"],
                question=q_data["question"],
                type=q_data["type"],
                options=q_data.get("options"),
                constraints=q_data.get("constraints"),
            ))

        await session.commit()

        result = await session.execute(select(OnboardingQuestion))
        all_questions = result.scalars().all()
        print(f"Seeded {len(all_questions)} questions successfully")

        steps: dict[str, int] = {}
        for q in all_questions:
            steps[q.step] = steps.get(q.step, 0) + 1

        print("\nQuestions by step:")
        for step, count in sorted(steps.items()):
            print(f"  {step}: {count}")


if __name__ == "__main__":
    asyncio.run(seed_questions())

