from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.core.logging import logger
from app.core.rate_limit import RateLimits, limiter
from app.models.user import User
from app.utils.jwt_utils import get_current_user
from app.schemas.diet import GenerateMealPlanRequest, MealPlanOut
from app.services.diet_ai_service import DietAIService
from app.services.onboarding_service import OnboardingService

router = APIRouter()


@router.post("/generate-meal-plan", response_model=MealPlanOut)
@limiter.limit(RateLimits.AI)
async def generate_meal_plan(
    payload: GenerateMealPlanRequest,
    request: Request,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    try:
        onboarding_service = OnboardingService(db)
        answers = await onboarding_service.get_user_answers_with_questions(current_user.id)
        wellness = await onboarding_service.get_wellness_metrics(current_user.id)

        user_data = {
            "age": current_user.age or 30,
            "gender": current_user.gender or "male",
            "weight": 70,
            "height": 170,
            "activity_level": "moderate",
        }

        if wellness.get("weight"):
            try:
                user_data["weight"] = float(str(wellness["weight"]).split()[0])
            except ValueError:
                pass

        if wellness.get("height"):
            height_str = str(wellness["height"])
            try:
                if "ft" in height_str.lower():
                    user_data["height"] = float(height_str.split()[0]) * 30.48
                elif "cm" in height_str.lower():
                    user_data["height"] = float(height_str.split()[0])
            except ValueError:
                pass

        activity_map = {
            "sedentary": "sedentary",
            "lightly active": "light",
            "moderately active": "moderate",
            "very active": "active",
            "extremely active": "very_active",
        }
        for answer in answers.get("answers", []):
            if "activity" in answer["question"].lower() or "exercise" in answer["question"].lower():
                answer_lower = str(answer["answer"]).lower()
                for key, value in activity_map.items():
                    if key in answer_lower:
                        user_data["activity_level"] = value
                        break

        meal_plan = DietAIService.generate_meal_plan(
            focus=payload.focus,
            user_data=user_data,
            calorie_target=payload.calorie_target,
            meal_count=payload.meal_count,
            snack_count=payload.snack_count,
            dietary_preferences=payload.dietary_preferences,
            allergies=payload.allergies,
            cuisine_preference=payload.cuisine_preference,
        )

        logger.info(f"Generated meal plan for user {current_user.id}: focus={payload.focus.value}, calories={meal_plan['calories']['intake']}")
        return meal_plan

    except ValueError as e:
        logger.error(f"Meal plan generation error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error generating meal plan: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to generate meal plan. Please try again.")

