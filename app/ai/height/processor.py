from typing import Any, Optional

from app.ai.gemini_client import GeminiError, run_gemini_json
from app.ai.height.prompts import build_context, prompt_height_full
from app.core.logging import logger


def _safe(data: dict, key: str, default: Any = None) -> Any:
    return data.get(key, default) if data else default


def _clean_exercises(items: list) -> list[dict]:
    cleaned = []
    for item in items[:5]:
        if isinstance(item, dict):
            steps = item.get("steps", [])
            cleaned.append({
                "seq":      item.get("seq", len(cleaned) + 1),
                "title":    item.get("title", ""),
                "duration": item.get("duration", "5 min"),
                "steps":    [str(s) for s in steps if s] if isinstance(steps, list) else [],
            })
        elif isinstance(item, str):
            parts = item.split(" — ")
            cleaned.append({
                "seq":      len(cleaned) + 1,
                "title":    parts[0].strip(),
                "duration": parts[1].strip() if len(parts) > 1 else "5 min",
                "steps":    [],
            })
    return cleaned


def normalize_attributes(data: dict) -> dict[str, str]:
    try:
        attrs = _safe(data, "attributes", {})
        return {
            "current_height":   attrs.get("current_height", "170 cm"),
            "goal_height":      attrs.get("goal_height", "175 cm"),
            "growth_potential": attrs.get("growth_potential", "Moderate"),
            "posture_status":   attrs.get("posture_status", "Average"),
            "bmi_status":       attrs.get("bmi_status", "Normal"),
        }
    except Exception as e:
        logger.error(f"Error normalizing height attributes: {e}")
        return {"current_height": "170 cm", "goal_height": "175 cm",
                "growth_potential": "Moderate", "posture_status": "Average", "bmi_status": "Normal"}


def normalize_progress_tracking(data: dict) -> dict[str, str]:
    try:
        progress = _safe(data, "progress_tracking", {})
        return {
            "completion_percent": progress.get("completion_percent", "0%"),
            "posture_gain_cm":    progress.get("posture_gain_cm", "0 cm"),
            "consistency":        progress.get("consistency", "0%"),
        }
    except Exception as e:
        logger.error(f"Error normalizing height progress tracking: {e}")
        return {"completion_percent": "0%", "posture_gain_cm": "0 cm", "consistency": "0%"}


def normalize_today_focus(data: dict) -> list[dict[str, str]]:
    try:
        today_focus = _safe(data, "today_focus", [])
        if not isinstance(today_focus, list):
            return []
        return [
            {"title": i.get("title", ""), "duration": i.get("duration", "5 min exercise")}
            for i in today_focus[:2] if isinstance(i, dict)
        ]
    except Exception as e:
        logger.error(f"Error normalizing height today focus: {e}")
        return []


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
        logger.error(f"Error normalizing height exercises: {e}")
        return {"morning": [], "evening": []}


def analyze_height(answers: list[dict], images: list[dict]) -> Optional[dict[str, Any]]:
    try:
        context = build_context(answers, images)
        raw = run_gemini_json(prompt_height_full(context), domain="height")

        if not raw:
            logger.warning("Empty response from Gemini for height analysis")
            return None

        return {
            "attributes":           normalize_attributes(raw),
            "progress_tracking":    normalize_progress_tracking(raw),
            "today_focus":          normalize_today_focus(raw),
            "daily_exercises":      normalize_exercises(raw),
            "motivational_message": raw.get("motivational_message", "Good posture can instantly improve your height appearance by up to 2-3 cm. Keep stretching daily!"),
        }
    except GeminiError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in height analysis: {e}", exc_info=True)
        return None

