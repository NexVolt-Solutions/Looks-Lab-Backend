"""
Seed onboarding questions into database.
Run once to populate the onboarding_questions table.
"""
import asyncio
import json
from pathlib import Path
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.onboarding import OnboardingQuestion
from app.core.logging import logger


async def seed_questions():
    """Load questions from JSON file and insert into database."""
    
    # Project root directory
    BASE_DIR = Path(__file__).resolve().parent.parent
    
    # Path to questions JSON
    json_path = BASE_DIR / "app" / "data" / "onboarding_questions.json"
    
    if not json_path.exists():
        logger.error(f"Questions file not found: {json_path}")
        print(f"? Questions file not found at: {json_path}")
        return
    
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Get questions from new flat structure
    questions_data = data.get("questions", [])
    
    if not questions_data:
        logger.error("No questions found in JSON file")
        print("? No questions found in JSON file")
        return
    
    print(f"?? Found {len(questions_data)} questions to seed")
    
    async with AsyncSessionLocal() as session:
        # Check if questions already exist
        result = await session.execute(select(OnboardingQuestion))
        existing = result.scalars().all()
        
        if existing:
            print(f"??  Database already has {len(existing)} questions")
            user_input = input("Delete and re-seed? (yes/no): ")
            
            if user_input.lower() != "yes":
                print("? Seeding cancelled")
                return
            
            # Delete existing questions
            for question in existing:
                await session.delete(question)
            await session.commit()
            print("???  Deleted existing questions")
        
        # Insert new questions
        created_count = 0
        
        for q_data in questions_data:
            question = OnboardingQuestion(
                step=q_data["step"],
                question=q_data["question"],
                type=q_data["type"],
                options=q_data.get("options"),
                constraints=q_data.get("constraints")
            )
            session.add(question)
            created_count += 1
        
        await session.commit()
        print(f"? Successfully seeded {created_count} questions!")
        
        # Verify
        result = await session.execute(select(OnboardingQuestion))
        all_questions = result.scalars().all()
        print(f"? Total questions in database: {len(all_questions)}")
        
        # Show breakdown by step
        steps = {}
        for q in all_questions:
            steps[q.step] = steps.get(q.step, 0) + 1
        
        print("\n?? Questions by step:")
        for step, count in sorted(steps.items()):
            print(f"  - {step}: {count} questions")


if __name__ == "__main__":
    asyncio.run(seed_questions())
    
    