from typing import Any, Optional

from app.ai.gemini_client import GeminiError, run_gemini_json
from app.ai.diet.prompts import build_context, prompt_diet_full
from app.core.logging import logger


def _safe(data: dict, key: str, default: Any = None) -> Any:
    return data.get(key, default) if data else default


def _clean_meals(items: list) -> list[dict]:
    cleaned = []
    for item in items[:5]:
        if isinstance(item, dict):
            cleaned.append({
                "seq":         item.get("seq", len(cleaned) + 1),
                "title":       item.get("title", ""),
                "description": item.get("description", ""),
                "time":        item.get("time", ""),
            })
        elif isinstance(item, str):
            cleaned.append({"seq": len(cleaned) + 1, "title": item, "description": "", "time": ""})
    return cleaned


def normalize_attributes(data: dict) -> dict[str, Any]:
    try:
        attrs = _safe(data, "attributes", {})
        today_focus  = attrs.get("today_focus", [])
        meals_summary = attrs.get("meals_summary", {})
        if not isinstance(meals_summary, dict):
            meals_summary = {}
        return {
            "calories_intake": attrs.get("calories_intake", "0 kcal"),
            "activity":        attrs.get("activity", "Moderate"),
            "goal":            attrs.get("goal", "Maintenance"),
            "diet_type":       attrs.get("diet_type", "Balanced"),
            "today_focus":     today_focus[:4] if isinstance(today_focus, list) else [],
            "posture_insight": attrs.get("posture_insight", "Consistency improves energy, digestion & overall health over time."),
            "meals_summary": {
                "total_meals":   meals_summary.get("total_meals", 3),
                "total_snacks":  meals_summary.get("total_snacks", 2),
                "prep_time_min": meals_summary.get("prep_time_min", 12),
            },
        }
    except Exception as e:
        logger.error(f"Error normalizing diet attributes: {e}")
        return {
            "calories_intake": "0 kcal", "activity": "Moderate", "goal": "Maintenance",
            "diet_type": "Balanced", "today_focus": [],
            "posture_insight": "Consistency improves energy, digestion & overall health.",
            "meals_summary": {"total_meals": 0, "total_snacks": 0, "prep_time_min": 0},
        }


def normalize_nutrition_targets(data: dict) -> dict[str, Any]:
    try:
        nutrition = _safe(data, "nutrition_targets", {})
        return {
            "daily_calories": nutrition.get("daily_calories", 2000),
            "protein_g":      nutrition.get("protein_g", 120),
            "carbs_g":        nutrition.get("carbs_g", 200),
            "fat_g":          nutrition.get("fat_g", 65),
            "water_glasses":  nutrition.get("water_glasses", 8),
            "fiber_g":        nutrition.get("fiber_g", 25),
        }
    except Exception as e:
        logger.error(f"Error normalizing diet nutrition targets: {e}")
        return {"daily_calories": 2000, "protein_g": 120, "carbs_g": 200, "fat_g": 65, "water_glasses": 8, "fiber_g": 25}


def normalize_routine(data: dict) -> dict[str, list[dict[str, Any]]]:
    try:
        routine = _safe(data, "routine", {})
        if not isinstance(routine, dict):
            return {"morning": [], "evening": []}
        return {
            "morning": _clean_meals(routine.get("morning", []) if isinstance(routine.get("morning"), list) else []),
            "evening": _clean_meals(routine.get("evening", []) if isinstance(routine.get("evening"), list) else []),
        }
    except Exception as e:
        logger.error(f"Error normalizing diet routine: {e}")
        return {"morning": [], "evening": []}


def normalize_progress_tracking(data: dict) -> dict[str, Any]:
    try:
        progress  = _safe(data, "progress_tracking", {})
        checklist = progress.get("recovery_checklist", [])
        return {
            "daily_calories":    progress.get("daily_calories", "0"),
            "consistency":       progress.get("consistency", "0%"),
            "nutrition_balance": progress.get("nutrition_balance", "0%"),
            "diet_consistency":  progress.get("diet_consistency", "0%"),
            "calorie_balance":   progress.get("calorie_balance", "0 / 2000"),
            "recovery_checklist": [str(i) for i in checklist[:4] if i] if isinstance(checklist, list) else [],
        }
    except Exception as e:
        logger.error(f"Error normalizing diet progress tracking: {e}")
        return {"daily_calories": "0", "consistency": "0%", "nutrition_balance": "0%",
                "diet_consistency": "0%", "calorie_balance": "0 / 2000", "recovery_checklist": []}


def analyze_diet(answers: list[dict], images: list[dict]) -> Optional[dict[str, Any]]:
    try:
        context = build_context(answers, images)
        raw = run_gemini_json(prompt_diet_full(context), domain="diet")

        if not raw:
            logger.warning("Empty response from Gemini for diet analysis")
            return None

        return {
            "attributes":           normalize_attributes(raw),
            "nutrition_targets":    normalize_nutrition_targets(raw),
            "routine":              normalize_routine(raw),
            "progress_tracking":    normalize_progress_tracking(raw),
            "motivational_message": raw.get("motivational_message", "Small daily diet improvements create long-term healthy habits. Keep going!"),
        }
    except GeminiError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in diet analysis: {e}", exc_info=True)
        return None

