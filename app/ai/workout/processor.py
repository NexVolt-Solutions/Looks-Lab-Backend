from typing import Any, Optional

from app.ai.gemini_client import GeminiError, run_gemini_json
from app.ai.workout.prompts import build_context, prompt_workout_full
from app.core.logging import logger


def _safe(data: dict, key: str, default: Any = None) -> Any:
    return data.get(key, default) if data else default


def _clean_exercises(items: list) -> list[dict]:
    cleaned = []
    for item in items[:5]:
        if isinstance(item, dict):
            steps = item.get("steps", [])
            cleaned.append({
                "seq": item.get("seq", len(cleaned) + 1),
                "title": item.get("title", ""),
                "duration": item.get("duration", "5 min"),
                "steps": [str(s) for s in steps if s] if isinstance(steps, list) else [],
            })
        elif isinstance(item, str):
            cleaned.append({"seq": len(cleaned) + 1, "title": item, "duration": "5 min", "steps": []})
    return cleaned


def normalize_attributes(data: dict) -> dict[str, Any]:
    try:
        attrs = _safe(data, "attributes", {})
        today_focus = attrs.get("today_focus", [])
        workout_summary = attrs.get("workout_summary", {})
        if not isinstance(workout_summary, dict):
            workout_summary = {}
        return {
            "intensity": attrs.get("intensity", "Moderate"),
            "activity": attrs.get("activity", "Moderate"),
            "goal": attrs.get("goal", "General Fitness"),
            "diet_type": attrs.get("diet_type", "Balanced"),
            "today_focus": today_focus[:4] if isinstance(today_focus, list) else [],
            "posture_insight": attrs.get("posture_insight", "Consistency improves stamina, strength & metabolism over time."),
            "workout_summary": {
                "total_exercises": workout_summary.get("total_exercises", 0),
                "total_duration_min": workout_summary.get("total_duration_min", 0),
            },
        }
    except Exception as e:
        logger.error(f"Error normalizing workout attributes: {e}")
        return {
            "intensity": "Moderate", "activity": "Moderate", "goal": "General Fitness",
            "diet_type": "Balanced", "today_focus": [],
            "posture_insight": "Consistency improves stamina, strength & metabolism over time.",
            "workout_summary": {"total_exercises": 0, "total_duration_min": 0},
        }


def normalize_exercises(data: dict) -> dict[str, list[dict[str, Any]]]:
    try:
        exercises = _safe(data, "exercises", {})
        if not isinstance(exercises, dict):
            exercises = {}
        return {
            "morning": _clean_exercises(exercises.get("morning", []) if isinstance(exercises.get("morning"), list) else []),
            "evening": _clean_exercises(exercises.get("evening", []) if isinstance(exercises.get("evening"), list) else []),
        }
    except Exception as e:
        logger.error(f"Error normalizing workout exercises: {e}")
        return {"morning": [], "evening": []}


def normalize_progress_tracking(data: dict) -> dict[str, Any]:
    try:
        progress = _safe(data, "progress_tracking", {})
        checklist = progress.get("recovery_checklist", [])
        return {
            "weekly_calories": progress.get("weekly_calories", "0"),
            "consistency": progress.get("consistency", "0%"),
            "strength_gain": progress.get("strength_gain", "0%"),
            "fitness_consistency": progress.get("fitness_consistency", "0%"),
            "recovery_checklist": [str(i) for i in checklist[:4] if i] if isinstance(checklist, list) else [],
        }
    except Exception as e:
        logger.error(f"Error normalizing workout progress tracking: {e}")
        return {"weekly_calories": "0", "consistency": "0%", "strength_gain": "0%", "fitness_consistency": "0%", "recovery_checklist": []}


def analyze_workout(answers: list[dict], images: list[dict]) -> Optional[dict[str, Any]]:
    try:
        context = build_context(answers, images)
        raw = run_gemini_json(prompt_workout_full(context), domain="workout")

        if not raw:
            logger.warning("Empty response from Gemini for workout analysis")
            return None

        return {
            "attributes": normalize_attributes(raw),
            "daily_exercises": normalize_exercises(raw),
            "progress_tracking": normalize_progress_tracking(raw),
            "motivational_message": raw.get("motivational_message", "Consistency improves stamina, strength & posture over time. Keep pushing!"),
        }
    except GeminiError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in workout analysis: {e}", exc_info=True)
        return None

