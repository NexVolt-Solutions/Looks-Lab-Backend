import json
from datetime import datetime, timezone
from typing import Optional

import google.generativeai as genai

from app.core.config import settings
from app.core.logging import logger
from app.schemas.diet import DietFocus

genai.configure(api_key=settings.GEMINI_API_KEY)


class DietAIService:

    @staticmethod
    def calculate_calorie_target(
        weight_kg: float,
        height_cm: float,
        age: int,
        gender: str,
        activity_level: str,
        focus: DietFocus,
    ) -> int:
        if gender.lower() == "male":
            bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) + 5
        else:
            bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) - 161

        activity_multipliers = {
            "sedentary": 1.2,
            "light": 1.375,
            "moderate": 1.55,
            "active": 1.725,
            "very_active": 1.9,
        }

        tdee = bmr * activity_multipliers.get(activity_level.lower(), 1.55)

        if focus == DietFocus.build_muscle:
            target = tdee + 300
        elif focus == DietFocus.fatloss:
            target = tdee - 500
        else:
            target = tdee

        return int(target)

    @staticmethod
    def generate_meal_plan(
        focus: DietFocus,
        user_data: dict,
        calorie_target: Optional[int] = None,
        meal_count: int = 3,
        snack_count: int = 2,
        dietary_preferences: Optional[list[str]] = None,
        allergies: Optional[list[str]] = None,
        cuisine_preference: Optional[str] = None,
    ) -> dict:
        if calorie_target is None:
            calorie_target = DietAIService.calculate_calorie_target(
                weight_kg=user_data.get("weight", 70),
                height_cm=user_data.get("height", 170),
                age=user_data.get("age", 30),
                gender=user_data.get("gender", "male"),
                activity_level=user_data.get("activity_level", "moderate"),
                focus=focus,
            )

        restrictions = []
        if dietary_preferences:
            restrictions.extend(dietary_preferences)
        if allergies:
            restrictions.extend([f"No {a}" for a in allergies])

        restrictions_str = ", ".join(restrictions) if restrictions else "None"
        cuisine_str = cuisine_preference or "Any"

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

MACRONUTRIENT TARGETS:
{DietAIService._get_macro_targets(focus, calorie_target)}

Generate a meal plan as a JSON object with this EXACT structure:
{{
  "focus": "{focus.value}",
  "title": "{focus.value.replace('_', ' ').title()} Meal Plan",
  "description": "Short motivational description",
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
      "macros": {{"protein": 30, "carbs": 50, "fats": 15}},
      "ingredients": ["Ingredient 1 with quantity"],
      "instructions": ["Step 1", "Step 2"],
      "benefits": "Why this meal supports the goal"
    }}
  ],
  "snacks": [
    {{
      "name": "Snack name",
      "prep_time_minutes": 5,
      "calories": 200,
      "macros": {{"protein": 10, "carbs": 20, "fats": 8}},
      "ingredients": ["Ingredient 1"],
      "instructions": ["Preparation step"]
    }}
  ],
  "daily_totals": {{
    "calories": {calorie_target},
    "protein": 150,
    "carbs": 200,
    "fats": 60
  }}
}}

Rules:
1. Meals must meet macronutrient targets
2. Keep prep times realistic (10-30 min meals, 2-10 min snacks)
3. Calculate total_prep_time_minutes as sum of all prep times
4. Ensure daily_totals match sum of all meals and snacks
5. Respect dietary preferences and allergies
6. Return ONLY valid JSON, no markdown or extra text
"""

        try:
            fresh_model = genai.GenerativeModel(settings.GEMINI_MODEL)
            response = fresh_model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=8192,
                    response_mime_type="application/json",
                )
            )

            response_text = response.text.strip()

            # Clean any markdown fences
            if "```json" in response_text:
                response_text = response_text.split("```json", 1)[1]
            if "```" in response_text:
                response_text = response_text.rsplit("```", 1)[0]

            # Extract JSON object
            start = response_text.find("{")
            end = response_text.rfind("}")
            if start != -1 and end != -1:
                response_text = response_text[start:end + 1]

            meal_plan = json.loads(response_text.strip())
            meal_plan["generated_at"] = datetime.now(timezone.utc).isoformat()

            logger.info(f"Generated meal plan for focus: {focus.value}")
            return meal_plan

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI meal plan response: {e}")
            raise ValueError("AI generated invalid meal plan format")
        except Exception as e:
            logger.error(f"Error generating meal plan: {e}")
            raise

    @staticmethod
    def _get_macro_targets(focus: DietFocus, calories: int) -> str:
        targets = {
            DietFocus.build_muscle: (0.30, 0.45, 0.25),
            DietFocus.fatloss:      (0.35, 0.35, 0.30),
            DietFocus.clean_energetic: (0.25, 0.50, 0.25),
            DietFocus.maintenance:  (0.30, 0.40, 0.30),
        }
        p, c, f = targets.get(focus, (0.30, 0.40, 0.30))
        return (
            f"- Protein: {int(p * 100)}% ({int(calories * p / 4)}g)\n"
            f"- Carbs: {int(c * 100)}% ({int(calories * c / 4)}g)\n"
            f"- Fats: {int(f * 100)}% ({int(calories * f / 9)}g)"
        )
        
        