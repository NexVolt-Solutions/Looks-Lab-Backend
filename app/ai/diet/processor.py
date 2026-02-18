"""
Diet domain AI processor.
Analyzes user diet data and generates personalized nutrition plans.
"""
from typing import Any

from app.ai.gemini_client import run_gemini_json, GeminiError
from app.ai.diet.prompts import prompt_diet_full, build_context
from app.core.logging import logger


def _get_safe_value(data: dict, key: str, default: Any = None) -> Any:
    return data.get(key, default) if data else default


def normalize_attributes(data: dict) -> dict[str, Any]:
    """
    Matches Figma Diet screen:
    Calories Intake, Activity, Today's Focus tags,
    Posture Insight, Today's Meals summary
    """
    try:
        attributes = _get_safe_value(data, "attributes", {})

        today_focus = attributes.get("today_focus", [])
        if not isinstance(today_focus, list):
            today_focus = []

        meals_summary = attributes.get("meals_summary", {})
        if not isinstance(meals_summary, dict):
            meals_summary = {}

        return {
            "calories_intake": attributes.get("calories_intake", "0 kcal"),
            "activity": attributes.get("activity", "Moderate"),
            "goal": attributes.get("goal", "Maintenance"),
            "diet_type": attributes.get("diet_type", "Balanced"),
            "today_focus": today_focus[:4],
            "posture_insight": attributes.get(
                "posture_insight",
                "Consistency improves energy, digestion & overall health over time."
            ),
            "meals_summary": {
                "total_meals": meals_summary.get("total_meals", 3),
                "total_snacks": meals_summary.get("total_snacks", 2),
                "prep_time_min": meals_summary.get("prep_time_min", 12)
            }
        }
    except Exception as e:
        logger.error(f"Error normalizing diet attributes: {str(e)}")
        return {
            "calories_intake": "0 kcal",
            "activity": "Moderate",
            "goal": "Maintenance",
            "diet_type": "Balanced",
            "today_focus": [],
            "posture_insight": "Consistency improves energy, digestion & overall health.",
            "meals_summary": {"total_meals": 0, "total_snacks": 0, "prep_time_min": 0}
        }


def normalize_nutrition_targets(data: dict) -> dict[str, Any]:
    """
    Matches Figma Track Your Nutrition screen:
    Daily calorie target, macros, water intake
    """
    try:
        nutrition = _get_safe_value(data, "nutrition_targets", {})

        return {
            "daily_calories": nutrition.get("daily_calories", 2000),
            "protein_g": nutrition.get("protein_g", 120),
            "carbs_g": nutrition.get("carbs_g", 200),
            "fat_g": nutrition.get("fat_g", 65),
            "water_glasses": nutrition.get("water_glasses", 8),
            "fiber_g": nutrition.get("fiber_g", 25),
        }
    except Exception as e:
        logger.error(f"Error normalizing diet nutrition targets: {str(e)}")
        return {
            "daily_calories": 2000,
            "protein_g": 120,
            "carbs_g": 200,
            "fat_g": 65,
            "water_glasses": 8,
            "fiber_g": 25,
        }


def normalize_routine(data: dict) -> dict[str, list[dict[str, Any]]]:
    """
    Matches Figma Daily Diet Routine screen:
    Morning Plan + Evening Plan
    Each meal: seq, title, description, time
    """
    try:
        routine = _get_safe_value(data, "routine", {})

        morning = routine.get("morning", [])
        evening = routine.get("evening", [])

        if not isinstance(morning, list):
            morning = []
        if not isinstance(evening, list):
            evening = []

        def clean_meals(items: list) -> list[dict]:
            cleaned = []
            for item in items[:5]:
                if isinstance(item, dict):
                    cleaned.append({
                        "seq": item.get("seq", len(cleaned) + 1),
                        "title": item.get("title", ""),
                        "description": item.get("description", ""),
                        "time": item.get("time", "")
                    })
                elif isinstance(item, str):
                    # Fallback for plain strings
                    cleaned.append({
                        "seq": len(cleaned) + 1,
                        "title": item,
                        "description": "",
                        "time": ""
                    })
            return cleaned

        return {
            "morning": clean_meals(morning),
            "evening": clean_meals(evening),
        }
    except Exception as e:
        logger.error(f"Error normalizing diet routine: {str(e)}")
        return {"morning": [], "evening": []}


def normalize_progress_tracking(data: dict) -> dict[str, Any]:
    """
    Matches Figma Your Progress screen:
    Daily Calorie, Consistency, Nutrition Balance,
    Diet Consistency chart, Recovery Checklist
    """
    try:
        progress = _get_safe_value(data, "progress_tracking", {})

        checklist = progress.get("recovery_checklist", [])
        if not isinstance(checklist, list):
            checklist = []

        return {
            "daily_calories": progress.get("daily_calories", "0"),
            "consistency": progress.get("consistency", "0%"),
            "nutrition_balance": progress.get("nutrition_balance", "0%"),
            "diet_consistency": progress.get("diet_consistency", "0%"),
            "calorie_balance": progress.get("calorie_balance", "0 / 2000"),
            "recovery_checklist": [
                str(item) for item in checklist[:4] if item
            ]
        }
    except Exception as e:
        logger.error(f"Error normalizing diet progress tracking: {str(e)}")
        return {
            "daily_calories": "0",
            "consistency": "0%",
            "nutrition_balance": "0%",
            "diet_consistency": "0%",
            "calorie_balance": "0 / 2000",
            "recovery_checklist": []
        }


def analyze_diet(answers: list[dict], images: list[dict]) -> dict[str, Any] | None:
    try:
        logger.info(
            f"Starting diet analysis with {len(answers)} answers "
            f"and {len(images)} images"
        )

        context = build_context(answers, images)
        prompt = prompt_diet_full(context)

        raw = run_gemini_json(prompt, domain="diet")

        if not raw:
            logger.warning("Empty response from Gemini for diet analysis")
            return None

        normalized = {
            "attributes": normalize_attributes(raw),
            "nutrition_targets": normalize_nutrition_targets(raw),
            "routine": normalize_routine(raw),
            "progress_tracking": normalize_progress_tracking(raw),
            "motivational_message": raw.get(
                "motivational_message",
                "Small daily diet improvements create long-term healthy habits. Keep going!"
            )
        }

        logger.info("Successfully completed diet analysis")
        return normalized

    except GeminiError as e:
        logger.error(f"Gemini AI error in diet analysis: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in diet analysis: {str(e)}", exc_info=True)
        return None

