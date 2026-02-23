"""Diet domain routes for AI-powered meal plan generation."""
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
    request: Request,  # noqa: ARG001
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generate personalized meal plan based on selected focus area.

    **Focus areas:**
    - `build_muscle`: High protein for muscle building
    - `maintenance`: Balanced macros for maintaining weight
    - `clean_energetic`: Clean eating with sustained energy
    - `fatloss`: Caloric deficit for weight loss

    **Returns:**
    AI-generated meal plan with meals, snacks, and complete macros

    **Example Request:**
```json
    {
      "focus": "build_muscle",
      "calorie_target": 2000,
      "meal_count": 3,
      "snack_count": 2,
      "dietary_preferences": ["vegetarian"],
      "allergies": ["nuts"],
      "cuisine_preference": "mediterranean"
    }
```
    """
    try:
        # Get user's onboarding data
        onboarding_service = OnboardingService(db)
        answers = await onboarding_service.get_user_answers_with_questions(
            current_user.id
        )
        wellness = await onboarding_service.get_wellness_metrics(current_user.id)

        # Extract user data
        user_data = {
            "age": current_user.age or 30,
            "gender": current_user.gender or "male",
            "weight": 70,  # Default in kg
            "height": 170,  # Default in cm
            "activity_level": "moderate",  # Default
        }

        # Extract from wellness metrics
        if wellness.get("weight"):
            # Parse weight (e.g., "76 kg" → 76)
            weight_str = str(wellness["weight"]).split()[0]
            try:
                user_data["weight"] = float(weight_str)
            except ValueError:
                pass

        if wellness.get("height"):
            # Parse height (e.g., "5.2 ft" → convert to cm)
            height_str = str(wellness["height"])
            if "ft" in height_str.lower():
                try:
                    feet = float(height_str.split()[0])
                    user_data["height"] = feet * 30.48  # Convert to cm
                except ValueError:
                    pass
            elif "cm" in height_str.lower():
                try:
                    user_data["height"] = float(height_str.split()[0])
                except ValueError:
                    pass

        # Extract from onboarding answers
        for answer in answers.get("answers", []):
            question_lower = answer["question"].lower()

            if "activity" in question_lower or "exercise" in question_lower:
                activity_map = {
                    "sedentary": "sedentary",
                    "lightly active": "light",
                    "moderately active": "moderate",
                    "very active": "active",
                    "extremely active": "very_active",
                }
                answer_lower = str(answer["answer"]).lower()
                for key, value in activity_map.items():
                    if key in answer_lower:
                        user_data["activity_level"] = value
                        break

        # Generate meal plan with AI (not async since Gemini SDK is sync)
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

        logger.info(
            f"Generated meal plan for user {current_user.id}: "
            f"focus={payload.focus.value}, calories={meal_plan['calories']['intake']}"
        )

        return meal_plan

    except ValueError as e:
        logger.error(f"Meal plan generation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error generating meal plan: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate meal plan. Please try again."
        )

