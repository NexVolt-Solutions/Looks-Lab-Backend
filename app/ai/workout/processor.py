"""
Workout domain AI processor.
Generates personalized fitness routines and workout plans.
"""
from typing import Any

from app.ai.gemini_client import run_gemini_json, GeminiError
from app.ai.workout.prompts import prompt_workout_full, build_context
from app.core.logging import logger


def _get_safe_value(data: dict, key: str, default: Any = None) -> Any:
    return data.get(key, default) if data else default


def normalize_attributes(data: dict) -> dict[str, Any]:
    """
    Matches Figma Workout screen:
    Intensity, Activity, Today's Focus tags,
    Posture Insight, Today's Workout summary
    """
    try:
        attributes = _get_safe_value(data, "attributes", {})

        today_focus = attributes.get("today_focus", [])
        if not isinstance(today_focus, list):
            today_focus = []

        workout_summary = attributes.get("workout_summary", {})
        if not isinstance(workout_summary, dict):
            workout_summary = {}

        return {
            "intensity": attributes.get("intensity", "Moderate"),
            "activity": attributes.get("activity", "Moderate"),
            "goal": attributes.get("goal", "General Fitness"),
            "diet_type": attributes.get("diet_type", "Balanced"),
            "today_focus": today_focus[:4],
            "posture_insight": attributes.get(
                "posture_insight",
                "Consistency improves stamina, strength & metabolism over time."
            ),
            "workout_summary": {
                "total_exercises": workout_summary.get("total_exercises", 0),
                "total_duration_min": workout_summary.get("total_duration_min", 0)
            }
        }
    except Exception as e:
        logger.error(f"Error normalizing workout attributes: {str(e)}")
        return {
            "intensity": "Moderate",
            "activity": "Moderate",
            "goal": "General Fitness",
            "diet_type": "Balanced",
            "today_focus": [],
            "posture_insight": "Consistency improves stamina, strength & metabolism over time.",
            "workout_summary": {"total_exercises": 0, "total_duration_min": 0}
        }


def normalize_exercises(data: dict) -> dict[str, list[dict[str, Any]]]:
    """
    Matches Figma Daily Workout Routine screen:
    Morning Plan + Evening Plan
    Each exercise: seq, title, duration, steps[]
    """
    try:
        exercises = _get_safe_value(data, "exercises", {})

        morning = exercises.get("morning", [])
        evening = exercises.get("evening", [])

        if not isinstance(morning, list):
            morning = []
        if not isinstance(evening, list):
            evening = []

        def clean_exercises(items: list) -> list[dict]:
            cleaned = []
            for item in items[:5]:
                if isinstance(item, dict):
                    steps = item.get("steps", [])
                    cleaned.append({
                        "seq": item.get("seq", len(cleaned) + 1),
                        "title": item.get("title", ""),
                        "duration": item.get("duration", "5 min"),
                        "steps": [str(s) for s in steps if s] if isinstance(steps, list) else []
                    })
                elif isinstance(item, str):
                    # Fallback for plain strings
                    cleaned.append({
                        "seq": len(cleaned) + 1,
                        "title": item,
                        "duration": "5 min",
                        "steps": []
                    })
            return cleaned

        return {
            "morning": clean_exercises(morning),
            "evening": clean_exercises(evening),
        }
    except Exception as e:
        logger.error(f"Error normalizing workout exercises: {str(e)}")
        return {"morning": [], "evening": []}


def normalize_progress_tracking(data: dict) -> dict[str, Any]:
    """
    Matches Figma Your Progress screen:
    Weekly Cal, Consistency, Strength gain,
    Fitness Consistency, Recovery Checklist
    """
    try:
        progress = _get_safe_value(data, "progress_tracking", {})

        checklist = progress.get("recovery_checklist", [])
        if not isinstance(checklist, list):
            checklist = []

        return {
            "weekly_calories": progress.get("weekly_calories", "0"),
            "consistency": progress.get("consistency", "0%"),
            "strength_gain": progress.get("strength_gain", "0%"),
            "fitness_consistency": progress.get("fitness_consistency", "0%"),
            "recovery_checklist": [
                str(item) for item in checklist[:4] if item
            ]
        }
    except Exception as e:
        logger.error(f"Error normalizing workout progress tracking: {str(e)}")
        return {
            "weekly_calories": "0",
            "consistency": "0%",
            "strength_gain": "0%",
            "fitness_consistency": "0%",
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
            "daily_exercises": normalize_exercises(raw),
            "progress_tracking": normalize_progress_tracking(raw),
            "motivational_message": raw.get(
                "motivational_message",
                "Consistency improves stamina, strength & posture over time. Keep pushing!"
            )
        }

        logger.info("Successfully completed workout analysis")
        return normalized

    except GeminiError as e:
        logger.error(f"Gemini AI error in workout analysis: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in workout analysis: {str(e)}", exc_info=True)
        return None

