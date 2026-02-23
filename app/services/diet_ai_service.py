"""Diet AI service for generating personalized meal plans."""
import google.generativeai as genai
import json
from datetime import datetime, timezone

from app.core.config import settings
from app.core.logging import logger
from app.schemas.diet import DietFocus

# Configure Gemini
genai.configure(api_key=settings.GEMINI_API_KEY)
model = genai.GenerativeModel(settings.GEMINI_MODEL)


class DietAIService:
    """Service for generating AI-powered meal plans."""

    @staticmethod
    def calculate_calorie_target(
        weight_kg: float,
        height_cm: float,
        age: int,
        gender: str,
        activity_level: str,
        focus: DietFocus,
    ) -> int:
        """
        Calculate target calories based on user profile and goals.
        Uses Mifflin-St Jeor Equation.
        """
        # Calculate BMR (Basal Metabolic Rate)
        if gender.lower() == "male":
            bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) + 5
        else:
            bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) - 161

        # Activity multipliers
        activity_multipliers = {
            "sedentary": 1.2,
            "light": 1.375,
            "moderate": 1.55,
            "active": 1.725,
            "very_active": 1.9,
        }

        # Calculate TDEE (Total Daily Energy Expenditure)
        tdee = bmr * activity_multipliers.get(activity_level.lower(), 1.55)

        # Adjust based on focus
        if focus == DietFocus.BUILD_MUSCLE:
            target = tdee + 300  # Caloric surplus
        elif focus == DietFocus.FATLOSS:
            target = tdee - 500  # Caloric deficit
        else:  # MAINTENANCE or CLEAN_ENERGETIC
            target = tdee

        return int(target)

    @staticmethod
    def generate_meal_plan(
        focus: DietFocus,
        user_data: dict,
        calorie_target: int | None = None,
        meal_count: int = 3,
        snack_count: int = 2,
        dietary_preferences: list[str] | None = None,
        allergies: list[str] | None = None,
        cuisine_preference: str | None = None,
    ) -> dict:
        """
        Generate personalized meal plan using Gemini AI.

        Args:
            focus: Diet focus area
            user_data: User profile and preferences
            calorie_target: Target daily calories (auto-calculated if None)
            meal_count: Number of main meals
            snack_count: Number of snacks
            dietary_preferences: List of dietary preferences
            allergies: List of allergies
            cuisine_preference: Preferred cuisine type

        Returns:
            Structured meal plan with meals and snacks
        """
        # Calculate calorie target if not provided
        if calorie_target is None:
            calorie_target = DietAIService.calculate_calorie_target(
                weight_kg=user_data.get("weight", 70),
                height_cm=user_data.get("height", 170),
                age=user_data.get("age", 30),
                gender=user_data.get("gender", "male"),
                activity_level=user_data.get("activity_level", "moderate"),
                focus=focus,
            )

        # Build dietary restrictions string
        restrictions = []
        if dietary_preferences:
            restrictions.extend(dietary_preferences)
        if allergies:
            restrictions.extend([f"No {allergy}" for allergy in allergies])

        restrictions_str = ", ".join(restrictions) if restrictions else "None"
        cuisine_str = cuisine_preference or "Any"

        # Build prompt
        prompt = f"""
You are a professional nutritionist creating a personalized meal plan.

USER PROFILE:
- Age: {user_data.get('age', 30)}
- Gender: {user_data.get('gender', 'Not specified')}
- Weight: {user_data.get('weight', 70)} kg
- Height: {user_data.get('height', 170)} cm
- Activity Level: {user_data.get('activity_level', 'moderate')}
- Dietary Preferences: {restrictions_str}
- Cuisine Preference: {cuisine_str}

MEAL PLAN REQUIREMENTS:
- Focus: {focus.value.replace('_', ' ').title()}
- Target Calories: {calorie_target} kcal/day
- Number of Meals: {meal_count}
- Number of Snacks: {snack_count}

MACRONUTRIENT TARGETS (based on focus):
{DietAIService._get_macro_targets(focus, calorie_target)}

Please generate a meal plan as a JSON object with this EXACT structure:
{{
  "focus": "{focus.value}",
  "title": "{focus.value.replace('_', ' ').title()} Meal Plan",
  "description": "Short motivational description (e.g., 'Improve strength & track your workout progress')",
  "calories": {{
    "intake": {calorie_target},
    "activity": "{user_data.get('activity_level', 'moderate')}"
  }},
  "insight": {{
    "title": "Nutrition Insight",
    "message": "Motivational message about consistency and health benefits"
  }},
  "meal_count": {meal_count},
  "snack_count": {snack_count},
  "total_prep_time_minutes": 0,
  "meals": [
    {{
      "type": "breakfast/lunch/dinner",
      "name": "Meal name",
      "prep_time_minutes": 15,
      "calories": 500,
      "macros": {{
        "protein": 30,
        "carbs": 50,
        "fats": 15
      }},
      "ingredients": [
        "Ingredient 1 with quantity",
        "Ingredient 2 with quantity"
      ],
      "instructions": [
        "Step 1",
        "Step 2"
      ],
      "benefits": "Why this meal is good for the focus area"
    }}
  ],
  "snacks": [
    {{
      "name": "Snack name",
      "prep_time_minutes": 5,
      "calories": 200,
      "macros": {{
        "protein": 10,
        "carbs": 20,
        "fats": 8
      }},
      "ingredients": [
        "Ingredient 1",
        "Ingredient 2"
      ],
      "instructions": [
        "Simple preparation step"
      ]
    }}
  ],
  "daily_totals": {{
    "calories": {calorie_target},
    "protein": 150,
    "carbs": 200,
    "fats": 60
  }}
}}

IMPORTANT REQUIREMENTS:
1. Ensure meals are balanced and meet macronutrient targets
2. Include variety in ingredients and cuisines
3. Keep prep times realistic (10-30 min for meals, 2-10 min for snacks)
4. Provide clear, step-by-step instructions
5. Calculate total_prep_time_minutes (sum of all prep times)
6. Ensure daily_totals match sum of all meals and snacks
7. Respect dietary preferences and allergies
8. Focus meals should align with the goal (e.g., high protein for build_muscle)
9. Return ONLY valid JSON, no markdown or extra text
"""

        try:
            # Generate with Gemini
            response = model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=3000,
                )
            )

            # Extract JSON from response
            response_text = response.text.strip()

            # Remove markdown code blocks if present
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]

            response_text = response_text.strip()

            # Parse JSON
            meal_plan = json.loads(response_text)

            # Add timestamp
            meal_plan["generated_at"] = datetime.now(timezone.utc).isoformat()

            logger.info(f"Generated meal plan for focus: {focus.value}")
            return meal_plan

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            logger.error(f"Response text: {response_text}")
            raise ValueError("AI generated invalid meal plan format")

        except Exception as e:
            logger.error(f"Error generating meal plan: {e}")
            raise

    @staticmethod
    def _get_macro_targets(focus: DietFocus, calories: int) -> str:
        """Get macronutrient distribution based on focus."""
        if focus == DietFocus.BUILD_MUSCLE:
            return f"""
- Protein: 30% ({int(calories * 0.30 / 4)}g)
- Carbs: 45% ({int(calories * 0.45 / 4)}g)
- Fats: 25% ({int(calories * 0.25 / 9)}g)
"""
        elif focus == DietFocus.FATLOSS:
            return f"""
- Protein: 35% ({int(calories * 0.35 / 4)}g)
- Carbs: 35% ({int(calories * 0.35 / 4)}g)
- Fats: 30% ({int(calories * 0.30 / 9)}g)
"""
        elif focus == DietFocus.CLEAN_ENERGETIC:
            return f"""
- Protein: 25% ({int(calories * 0.25 / 4)}g)
- Carbs: 50% ({int(calories * 0.50 / 4)}g)
- Fats: 25% ({int(calories * 0.25 / 9)}g)
"""
        else:  # MAINTENANCE
            return f"""
- Protein: 30% ({int(calories * 0.30 / 4)}g)
- Carbs: 40% ({int(calories * 0.40 / 4)}g)
- Fats: 30% ({int(calories * 0.30 / 9)}g)
"""

