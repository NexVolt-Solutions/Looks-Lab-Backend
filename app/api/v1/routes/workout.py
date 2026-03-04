from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.core.logging import logger
from app.core.rate_limit import RateLimits, limiter
from app.models.user import User
from app.utils.jwt_utils import get_current_user
from app.schemas.workout import GenerateWorkoutRequest, WorkoutPlanOut
from app.services.workout_ai_service import WorkoutAIService
from app.services.onboarding_service import OnboardingService

router = APIRouter()


@router.post("/generate-plan", response_model=WorkoutPlanOut)
@limiter.limit(RateLimits.AI)
async def generate_workout_plan(
    payload: GenerateWorkoutRequest,
    request: Request,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    try:
        answers = await OnboardingService(db).get_user_answers_with_questions(current_user.id)

        user_data = {
            "age": current_user.age,
            "gender": current_user.gender,
            "fitness_level": "beginner",
            "workout_frequency": "3 times per week",
            "equipment": "None",
            "goals": "General fitness",
        }

        for answer in answers.get("answers", []):
            question_lower = answer["question"].lower()
            if "fitness level" in question_lower or "experience" in question_lower:
                user_data["fitness_level"] = str(answer["answer"])
            elif "workout" in question_lower and "frequency" in question_lower:
                user_data["workout_frequency"] = str(answer["answer"])
            elif "equipment" in question_lower:
                user_data["equipment"] = str(answer["answer"])
            elif "goal" in question_lower:
                user_data["goals"] = str(answer["answer"])

        workout_plan = WorkoutAIService.generate_workout_plan(
            focus=payload.focus,
            user_data=user_data,
            intensity=payload.intensity,
            duration_minutes=payload.duration_minutes,
        )

        logger.info(f"Generated workout plan for user {current_user.id}: focus={payload.focus.value}, duration={payload.duration_minutes}min")
        return workout_plan

    except ValueError as e:
        logger.error(f"Workout plan generation error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error generating workout plan: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to generate workout plan. Please try again.")

