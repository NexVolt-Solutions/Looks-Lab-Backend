"""
Diet domain AI processor.
Analyzes user diet data and generates personalized nutrition plans.
"""
from typing import Any

from app.ai.gemini_client import run_gemini_json, GeminiError
from app.ai.diet.prompts import prompt_diet_full
from app.core.logging import logger


def build_context(answers: list[dict], images: list[dict]) -> dict:
    return {
        "answers": [
            {
                "step": a.get("step"),
                "question": a.get("question"),
                "answer": a.get("answer")
            }
            for a in answers
        ],
        "images": [
            {
                "view": i.get("view"),
                "present": bool(i.get("url"))
            }
            for i in images
        ],
    }


def _get_safe_value(data: dict, key: str, default: Any = None) -> Any:
    return data.get(key, default) if data else default


def normalize_attributes(data: dict) -> dict[str, str]:
    try:
        attributes = _get_safe_value(data, "attributes", {})

        return {
            "diet_type": attributes.get("diet_type", "Balanced"),
            "goal": attributes.get("goal", "Maintenance"),
            "activity_level": attributes.get("activity_level", "Moderate"),
            "hydration": attributes.get("hydration", "1-2L"),
        }
    except Exception as e:
        logger.error(f"Error normalizing diet attributes: {str(e)}")
        return {
            "diet_type": "Balanced",
            "goal": "Maintenance",
            "activity_level": "Moderate",
            "hydration": "1-2L",
        }


def normalize_nutrition_summary(data: dict) -> dict[str, Any]:
    try:
        nutrition = _get_safe_value(data, "nutrition_summary", {})

        return {
            "calories": nutrition.get("calories", 2000),
            "protein": nutrition.get("protein", "100g"),
            "carbs": nutrition.get("carbs", "200g"),
            "portion_size": nutrition.get("portion_size", "300g"),
        }
    except Exception as e:
        logger.error(f"Error normalizing diet nutrition summary: {str(e)}")
        return {
            "calories": 2000,
            "protein": "100g",
            "carbs": "200g",
            "portion_size": "300g",
        }


def normalize_daily_routine(data: dict) -> dict[str, list[str]]:
    try:
        routine = _get_safe_value(data, "daily_routine", {})

        morning = routine.get("morning", [])
        evening = routine.get("evening", [])

        if not isinstance(morning, list):
            morning = []
        if not isinstance(evening, list):
            evening = []

        return {
            "morning": morning[:5],
            "evening": evening[:5],
        }
    except Exception as e:
        logger.error(f"Error normalizing diet routine: {str(e)}")
        return {
            "morning": [],
            "evening": [],
        }


def normalize_progress_tracking(data: dict) -> dict[str, Any]:
    try:
        progress = _get_safe_value(data, "progress_tracking", {})

        checklist = progress.get("recovery_checklist", [])
        if not isinstance(checklist, list):
            checklist = []

        return {
            "calorie_balance": progress.get("calorie_balance", "0 / 2000"),
            "diet_consistency": progress.get("diet_consistency", "0%"),
            "recovery_checklist": checklist[:5]
        }
    except Exception as e:
        logger.error(f"Error normalizing diet progress tracking: {str(e)}")
        return {
            "calorie_balance": "0 / 2000",
            "diet_consistency": "0%",
            "recovery_checklist": []
        }


def analyze_diet(answers: list[dict], images: list[dict]) -> dict[str, Any] | None:
    try:
        logger.info(f"Starting diet analysis with {len(answers)} answers and {len(images)} images")

        context = build_context(answers, images)
        prompt = prompt_diet_full(context)

        raw = run_gemini_json(prompt, domain="diet")

        if not raw:
            logger.warning("Empty response from Gemini for diet analysis")
            return None

        normalized = {
            "attributes": normalize_attributes(raw),
            "nutrition_summary": normalize_nutrition_summary(raw),
            "daily_routine": normalize_daily_routine(raw),
            "progress_tracking": normalize_progress_tracking(raw),
            "motivational_message": raw.get("motivational_message", "Small daily improvements lead to great results!")
        }

        logger.info("Successfully completed diet analysis")
        return normalized

    except GeminiError as e:
        logger.error(f"Gemini AI error in diet analysis: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in diet analysis: {str(e)}", exc_info=True)
        return None

