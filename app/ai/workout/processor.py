"""
Workout domain AI processor.
Generates personalized fitness routines and workout plans.
"""
from typing import Any

from app.ai.gemini_client import run_gemini_json, GeminiError
from app.ai.workout.prompts import prompt_workout_full
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
        "images": []
    }


def _get_safe_value(data: dict, key: str, default: Any = None) -> Any:
    return data.get(key, default) if data else default


def normalize_attributes(data: dict) -> dict[str, Any]:
    try:
        attributes = _get_safe_value(data, "attributes", {})

        focus_tags = attributes.get("focus_tags", [])
        if not isinstance(focus_tags, list):
            focus_tags = []

        return {
            "activity_level": attributes.get("activity_level", "Moderate"),
            "hydration": attributes.get("hydration", "1-2L"),
            "goal": attributes.get("goal", "Maintenance"),
            "diet_type": attributes.get("diet_type", "Balanced"),
            "focus_tags": focus_tags[:4]
        }
    except Exception as e:
        logger.error(f"Error normalizing workout attributes: {str(e)}")
        return {
            "activity_level": "Moderate",
            "hydration": "1-2L",
            "goal": "Maintenance",
            "diet_type": "Balanced",
            "focus_tags": []
        }


def normalize_routine(data: dict) -> dict[str, list[dict[str, str]]]:
    try:
        routine = _get_safe_value(data, "routine", {})

        morning = routine.get("morning", [])
        evening = routine.get("evening", [])

        if not isinstance(morning, list):
            morning = []
        if not isinstance(evening, list):
            evening = []

        normalized_morning = []
        for ex in morning[:5]:
            if isinstance(ex, dict):
                normalized_morning.append({
                    "name": ex.get("name", "Exercise"),
                    "duration": ex.get("duration", "5 min"),
                    "instructions": ex.get("instructions", "")
                })

        normalized_evening = []
        for ex in evening[:5]:
            if isinstance(ex, dict):
                normalized_evening.append({
                    "name": ex.get("name", "Exercise"),
                    "duration": ex.get("duration", "5 min"),
                    "instructions": ex.get("instructions", "")
                })

        return {
            "morning": normalized_morning,
            "evening": normalized_evening,
        }
    except Exception as e:
        logger.error(f"Error normalizing workout routine: {str(e)}")
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
            "weekly_calories": progress.get("weekly_calories", "0 kcal"),
            "consistency": progress.get("consistency", "0%"),
            "strength_gain": progress.get("strength_gain", "0%"),
            "recovery_checklist": checklist[:5]
        }
    except Exception as e:
        logger.error(f"Error normalizing workout progress tracking: {str(e)}")
        return {
            "weekly_calories": "0 kcal",
            "consistency": "0%",
            "strength_gain": "0%",
            "recovery_checklist": []
        }


def analyze_workout(answers: list[dict], images: list[dict]) -> dict[str, Any] | None:
    try:
        logger.info(f"Starting workout analysis with {len(answers)} answers")

        context = build_context(answers, images)
        prompt = prompt_workout_full(context)

        raw = run_gemini_json(prompt, domain="workout")

        if not raw:
            logger.warning("Empty response from Gemini for workout analysis")
            return None

        normalized = {
            "attributes": normalize_attributes(raw),
            "routine": normalize_routine(raw),
            "progress_tracking": normalize_progress_tracking(raw),
            "motivational_message": raw.get("motivational_message",
                                            "Consistency is key to achieving your fitness goals!")
        }

        logger.info("Successfully completed workout analysis")
        return normalized

    except GeminiError as e:
        logger.error(f"Gemini AI error in workout analysis: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in workout analysis: {str(e)}", exc_info=True)
        return None

