from typing import Any, Optional

from app.ai.gemini_client import GeminiError, run_gemini_json
from app.ai.workout.prompts import build_context, prompt_workout_full
from app.core.logging import logger


def _safe(data: dict, key: str, default: Any = None) -> Any:
    return data.get(key, default) if data else default


def _normalize_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text or default


def _coerce_int(value: Any, default: int) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _default_today_focus() -> list[str]:
    return ["Flexibility", "Build Muscle", "Fatloss", "Strength"]


def _default_posture_insight() -> dict[str, str]:
    return {
        "title": "Posture Insight",
        "message": "Consistency improves stamina, strength, and posture over time.",
    }


def _default_exercises() -> dict[str, list[dict[str, Any]]]:
    return {
        "morning": [
            {
                "seq": 1,
                "title": "Jumping Jacks",
                "duration": "5 min",
                "steps": [
                    "Stand tall and begin with a steady pace.",
                    "Keep your breathing controlled throughout the movement.",
                ],
            },
            {
                "seq": 2,
                "title": "Bodyweight Squats",
                "duration": "5 min",
                "steps": [
                    "Lower with control while keeping the chest lifted.",
                    "Drive through the heels to return to standing.",
                ],
            },
            {
                "seq": 3,
                "title": "Arm Circles",
                "duration": "2 min",
                "steps": [
                    "Extend the arms and rotate in small circles.",
                    "Reverse direction halfway through the set.",
                ],
            },
        ],
        "evening": [
            {
                "seq": 1,
                "title": "Brisk Walk or Warmup",
                "duration": "5 min",
                "steps": [
                    "Move continuously at a comfortable pace.",
                    "Loosen the shoulders and hips while breathing evenly.",
                ],
            },
            {
                "seq": 2,
                "title": "Plank",
                "duration": "2 min",
                "steps": [
                    "Keep the body in a straight line.",
                    "Brace the core and breathe steadily.",
                ],
            },
            {
                "seq": 3,
                "title": "Stretching",
                "duration": "5 min",
                "steps": [
                    "Move through the main muscle groups gently.",
                    "Hold each stretch briefly without forcing range.",
                ],
            },
        ],
    }


def _default_progress_tracking() -> dict[str, Any]:
    return {
        "weekly_calories": "2300",
        "consistency": "85%",
        "strength_gain": "+12%",
        "fitness_consistency": "85%",
        "recovery_checklist": [
            "Got 7+ hours of sleep",
            "Drank 8+ glasses of water",
            "Stretched for 10 minutes",
            "Took a rest if needed",
        ],
    }


def _clean_exercises(items: list) -> list[dict[str, Any]]:
    cleaned: list[dict[str, Any]] = []
    for item in items[:5]:
        if isinstance(item, dict):
            steps = item.get("steps", [])
            cleaned.append({
                "seq": _coerce_int(item.get("seq"), len(cleaned) + 1),
                "title": _normalize_text(item.get("title")),
                "duration": _normalize_text(item.get("duration"), "5 min"),
                "steps": [
                    _normalize_text(step) for step in steps
                    if _normalize_text(step)
                ] if isinstance(steps, list) else [],
            })
        elif isinstance(item, str) and item.strip():
            cleaned.append({
                "seq": len(cleaned) + 1,
                "title": item.strip(),
                "duration": "5 min",
                "steps": [],
            })
    return cleaned


def normalize_attributes(data: dict) -> dict[str, Any]:
    try:
        attrs = _safe(data, "attributes", {})
        today_focus = attrs.get("today_focus", [])
        workout_summary = attrs.get("workout_summary", {})
        if not isinstance(workout_summary, dict):
            workout_summary = {}
        normalized_focus = [
            _normalize_text(item) for item in today_focus[:4]
            if _normalize_text(item)
        ] if isinstance(today_focus, list) else []
        if not normalized_focus:
            normalized_focus = _default_today_focus()
        posture_insight = attrs.get("posture_insight")
        if isinstance(posture_insight, dict):
            normalized_posture = {
                "title": _normalize_text(posture_insight.get("title"), "Posture Insight"),
                "message": _normalize_text(
                    posture_insight.get("message"),
                    "Consistency improves stamina, strength, and posture over time.",
                ),
            }
        else:
            normalized_posture = _default_posture_insight()
        return {
            "intensity": _normalize_text(attrs.get("intensity"), "Moderate"),
            "activity": _normalize_text(attrs.get("activity"), "Moderate"),
            "goal": _normalize_text(attrs.get("goal"), "General Fitness"),
            "today_focus": normalized_focus,
            "posture_insight": normalized_posture,
            "workout_summary": {
                "total_exercises": _coerce_int(workout_summary.get("total_exercises"), 6),
                "total_duration_min": _coerce_int(workout_summary.get("total_duration_min"), 22),
            },
        }
    except Exception as e:
        logger.error(f"Error normalizing workout attributes: {e}")
        return {
            "intensity": "Moderate",
            "activity": "Moderate",
            "goal": "General Fitness",
            "today_focus": _default_today_focus(),
            "posture_insight": _default_posture_insight(),
            "workout_summary": {"total_exercises": 6, "total_duration_min": 22},
        }


def normalize_exercises(data: dict) -> dict[str, list[dict[str, Any]]]:
    try:
        exercises = _safe(data, "exercises", {})
        if not isinstance(exercises, dict):
            return _default_exercises()
        normalized = {
            "morning": _clean_exercises(exercises.get("morning", []) if isinstance(exercises.get("morning"), list) else []),
            "evening": _clean_exercises(exercises.get("evening", []) if isinstance(exercises.get("evening"), list) else []),
        }
        defaults = _default_exercises()
        if not normalized["morning"]:
            normalized["morning"] = defaults["morning"]
        if not normalized["evening"]:
            normalized["evening"] = defaults["evening"]
        return normalized
    except Exception as e:
        logger.error(f"Error normalizing workout exercises: {e}")
        return _default_exercises()


def normalize_progress_tracking(data: dict) -> dict[str, Any]:
    try:
        progress = _safe(data, "progress_tracking", {})
        checklist = progress.get("recovery_checklist", [])
        normalized_checklist = [
            _normalize_text(item) for item in checklist[:4]
            if _normalize_text(item)
        ] if isinstance(checklist, list) else []
        defaults = _default_progress_tracking()
        return {
            "weekly_calories": _normalize_text(progress.get("weekly_calories"), defaults["weekly_calories"]),
            "consistency": _normalize_text(progress.get("consistency"), defaults["consistency"]),
            "strength_gain": _normalize_text(progress.get("strength_gain"), defaults["strength_gain"]),
            "fitness_consistency": _normalize_text(progress.get("fitness_consistency"), defaults["fitness_consistency"]),
            "recovery_checklist": normalized_checklist or defaults["recovery_checklist"],
        }
    except Exception as e:
        logger.error(f"Error normalizing workout progress tracking: {e}")
        return _default_progress_tracking()


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
            "motivational_message": _normalize_text(
                raw.get("motivational_message"),
                "Consistency improves stamina, strength and posture over time. Keep pushing!",
            ),
        }
    except GeminiError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in workout analysis: {e}", exc_info=True)
        return None
