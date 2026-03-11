import asyncio
import json
from pathlib import Path
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.core.logging import logger
from app.models.onboarding import OnboardingQuestion
from app.models.domain import DomainQuestion, QuestionType

BASE_DIR = Path(__file__).resolve().parent.parent
ONBOARDING_JSON = BASE_DIR / "app" / "data" / "onboarding_questions.json"
DOMAIN_JSON = BASE_DIR / "app" / "data" / "domain_questions.json"

TYPE_MAP = {
    "text":         QuestionType.text,
    "choice":       QuestionType.choice,
    "multi_choice": QuestionType.multi_choice,
    "numeric":      QuestionType.numeric,
}


async def seed_onboarding_questions(session) -> None:
    if not ONBOARDING_JSON.exists():
        logger.error(f"Onboarding questions file not found: {ONBOARDING_JSON}")
        print(f"File not found: {ONBOARDING_JSON}")
        return

    with open(ONBOARDING_JSON, encoding="utf-8") as f:
        data = json.load(f)

    questions_data = data.get("questions", [])
    if not questions_data:
        print("No onboarding questions found in JSON file")
        return

    print(f"\nFound {len(questions_data)} onboarding questions to seed")

    result = await session.execute(select(OnboardingQuestion))
    existing = result.scalars().all()

    if existing:
        print(f"Database already has {len(existing)} onboarding questions")
        if input("Delete and re-seed onboarding questions? (yes/no): ").lower() != "yes":
            print("Skipping onboarding questions")
            return
        for q in existing:
            await session.delete(q)
        await session.commit()
        print("Deleted existing onboarding questions")

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
    print(f"Seeded {len(all_questions)} onboarding questions successfully")

    steps: dict[str, int] = {}
    for q in all_questions:
        steps[q.step] = steps.get(q.step, 0) + 1
    print("\nOnboarding questions by step:")
    for step, count in sorted(steps.items()):
        print(f"  {step}: {count}")


async def seed_domain_questions(session) -> None:
    if not DOMAIN_JSON.exists():
        logger.error(f"Domain questions file not found: {DOMAIN_JSON}")
        print(f"File not found: {DOMAIN_JSON}")
        return

    with open(DOMAIN_JSON, encoding="utf-8") as f:
        data = json.load(f)

    domains = data.get("domains", {})
    if not domains:
        print("No domain questions found in JSON file")
        return

    total = sum(len(qs) for qs in domains.values())
    print(f"\nFound {len(domains)} domains with {total} total questions to seed")

    result = await session.execute(select(DomainQuestion))
    existing = result.scalars().all()

    if existing:
        print(f"Database already has {len(existing)} domain questions")
        if input("Delete and re-seed domain questions? (yes/no): ").lower() != "yes":
            print("Skipping domain questions")
            return
        for q in existing:
            await session.delete(q)
        await session.commit()
        print("Deleted existing domain questions")

    for domain, questions in domains.items():
        for idx, q_data in enumerate(questions, start=1):
            session.add(DomainQuestion(
                domain=domain,
                step=q_data.get("step"),          
                question=q_data["question"],
                type=TYPE_MAP.get(q_data["type"], QuestionType.text),
                options=q_data.get("options"),
                constraints=q_data.get("constraints"),
                seq=idx,
            ))

    await session.commit()

    result = await session.execute(select(DomainQuestion))
    all_questions = result.scalars().all()
    print(f"Seeded {len(all_questions)} domain questions successfully")

    counts: dict[str, int] = {}
    for q in all_questions:
        counts[q.domain] = counts.get(q.domain, 0) + 1
    print("\nDomain questions by domain:")
    for domain, count in sorted(counts.items()):
        print(f"  {domain}: {count}")


async def seed_all() -> None:
    async with AsyncSessionLocal() as session:
        await seed_onboarding_questions(session)
        await seed_domain_questions(session)


if __name__ == "__main__":
    asyncio.run(seed_all())
    
    