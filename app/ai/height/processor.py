from typing import Any, Optional

from app.ai.gemini_client import GeminiError, run_gemini_json
from app.ai.height.prompts import build_context, prompt_height_full
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


def _default_attributes() -> dict[str, str]:
    return {
        "current_height": "170 cm",
        "goal_height": "175 cm",
        "growth_potential": "Moderate",
        "posture_status": "Average",
        "bmi_status": "Normal",
    }


def _default_progress_tracking() -> dict[str, str]:
    return {
        "completion_percent": "40%",
        "posture_gain_cm": "2.5 cm",
        "consistency": "85%",
    }


def _default_today_focus() -> list[dict[str, str]]:
    return [
        {"title": "Neck Stretches", "duration": "5 min exercise"},
        {"title": "Spine Alignment", "duration": "5 min exercise"},
    ]


def _default_exercises() -> dict[str, list[dict[str, Any]]]:
    return {
        "morning": [
            {
                "seq": 1,
                "title": "Cat-Cow Stretch",
                "duration": "5 min",
                "steps": [
                    "Move slowly with your breath while mobilizing the spine.",
                    "Keep the movement controlled and comfortable.",
                ],
            },
            {
                "seq": 2,
                "title": "Cobra Pose",
                "duration": "5 min",
                "steps": [
                    "Lift the chest gently without forcing the lower back.",
                    "Relax the shoulders and breathe steadily.",
                ],
            },
            {
                "seq": 3,
                "title": "Hanging Exercise",
                "duration": "5 min",
                "steps": [
                    "Let the body lengthen while keeping the grip comfortable.",
                    "Come down slowly and rest when needed.",
                ],
            },
            {
                "seq": 4,
                "title": "Neck Rolls",
                "duration": "5 min",
                "steps": [
                    "Move gently through the neck range without forcing it.",
                    "Reverse direction after a few smooth repetitions.",
                ],
            },
        ],
        "evening": [
            {
                "seq": 1,
                "title": "Spine Decompression",
                "duration": "5 min",
                "steps": [
                    "Relax into the stretch and breathe deeply.",
                    "Release slowly between repetitions.",
                ],
            },
            {
                "seq": 2,
                "title": "Wall Angles",
                "duration": "5 min",
                "steps": [
                    "Keep the upper back tall and move with control.",
                    "Avoid shrugging the shoulders.",
                ],
            },
            {
                "seq": 3,
                "title": "Child's Pose",
                "duration": "5 min",
                "steps": [
                    "Sink into the stretch comfortably.",
                    "Focus on slow breathing and relaxation.",
                ],
            },
            {
                "seq": 4,
                "title": "Leg Stretches",
                "duration": "5 min",
                "steps": [
                    "Stretch each side evenly without bouncing.",
                    "Keep the spine long while reaching gently.",
                ],
            },
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


def normalize_attributes(data: dict) -> dict[str, str]:
    try:
        attrs = _safe(data, "attributes", {})
        defaults = _default_attributes()
        return {
            "current_height": _normalize_text(attrs.get("current_height"), defaults["current_height"]),
            "goal_height": _normalize_text(attrs.get("goal_height"), defaults["goal_height"]),
            "growth_potential": _normalize_text(attrs.get("growth_potential"), defaults["growth_potential"]),
            "posture_status": _normalize_text(attrs.get("posture_status"), defaults["posture_status"]),
            "bmi_status": _normalize_text(attrs.get("bmi_status"), defaults["bmi_status"]),
        }
    except Exception as e:
        logger.error(f"Error normalizing height attributes: {e}")
        return _default_attributes()


def normalize_progress_tracking(data: dict) -> dict[str, str]:
    try:
        progress = _safe(data, "progress_tracking", {})
        defaults = _default_progress_tracking()
        return {
            "completion_percent": _normalize_text(progress.get("completion_percent"), defaults["completion_percent"]),
            "posture_gain_cm": _normalize_text(progress.get("posture_gain_cm"), defaults["posture_gain_cm"]),
            "consistency": _normalize_text(progress.get("consistency"), defaults["consistency"]),
        }
    except Exception as e:
        logger.error(f"Error normalizing height progress tracking: {e}")
        return _default_progress_tracking()


def normalize_today_focus(data: dict) -> list[dict[str, str]]:
    try:
        today_focus = _safe(data, "today_focus", [])
        if not isinstance(today_focus, list):
            return _default_today_focus()
        cleaned = [
            {
                "title": _normalize_text(item.get("title")),
                "duration": _normalize_text(item.get("duration"), "5 min exercise"),
            }
            for item in today_focus[:2]
            if isinstance(item, dict) and (_normalize_text(item.get("title")) or _normalize_text(item.get("duration")))
        ]
        return cleaned or _default_today_focus()
    except Exception as e:
        logger.error(f"Error normalizing height today focus: {e}")
        return _default_today_focus()


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
        logger.error(f"Error normalizing height exercises: {e}")
        return _default_exercises()


def analyze_height(answers: list[dict], images: list[dict]) -> Optional[dict[str, Any]]:
    try:
        context = build_context(answers, images)
        raw = run_gemini_json(prompt_height_full(context), domain="height")

        if not raw:
            logger.warning("Empty response from Gemini for height analysis")
            return None

        return {
            "attributes": normalize_attributes(raw),
            "progress_tracking": normalize_progress_tracking(raw),
            "today_focus": normalize_today_focus(raw),
            "daily_exercises": normalize_exercises(raw),
            "motivational_message": _normalize_text(
                raw.get("motivational_message"),
                "Good posture can improve your height appearance. Keep stretching daily!",
            ),
        }
    except GeminiError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in height analysis: {e}", exc_info=True)
        return None
