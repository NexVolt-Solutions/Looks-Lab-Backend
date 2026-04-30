from typing import Any, Optional

from app.ai.diet.prompts import build_context, prompt_diet_full
from app.ai.gemini_client import GeminiError, run_gemini_json
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
    return ["Build Muscle", "Maintenance", "Clean & Energetic Diet", "Fatloss"]


def _default_nutrition_targets() -> dict[str, Any]:
    return {
        "daily_calories": 2000,
        "protein_g": 120,
        "carbs_g": 200,
        "fat_g": 65,
        "water_glasses": 8,
        "fiber_g": 25,
    }


def _default_routine() -> dict[str, list[dict[str, Any]]]:
    return {
        "morning": [
            {
                "seq": 1,
                "title": "Breakfast",
                "subtitle": "Oatmeal with fruits and nuts",
                "description": "Balanced carbs and fiber to support steady morning energy.",
                "duration": "10 min",
            },
            {
                "seq": 2,
                "title": "Morning Snack",
                "subtitle": "Yogurt or smoothie",
                "description": "Add protein early to help control cravings before lunch.",
                "duration": "5 min",
            },
            {
                "seq": 3,
                "title": "Hydration",
                "subtitle": "Drink 1 glass of water",
                "description": "Start hydration early to support digestion and focus.",
                "duration": "1 min",
            },
        ],
        "evening": [
            {
                "seq": 1,
                "title": "Lunch",
                "subtitle": "Balanced plate with protein, vegetables, and carbs",
                "description": "Keep portions steady and avoid sugary drinks.",
                "duration": "20 min",
            },
            {
                "seq": 2,
                "title": "Afternoon Snack",
                "subtitle": "Fruit or nuts",
                "description": "Use whole foods to reduce evening overeating.",
                "duration": "5 min",
            },
            {
                "seq": 3,
                "title": "Dinner",
                "subtitle": "Light, easy-to-digest meal",
                "description": "Prefer an earlier, lighter dinner when possible.",
                "duration": "20 min",
            },
        ],
    }


def _default_progress_tracking() -> dict[str, Any]:
    return {
        "daily_calories": "2300",
        "consistency": "85%",
        "nutrition_balance": "+12%",
        "diet_consistency": "85%",
        "calorie_balance": "1420 / 2000",
        "recovery_checklist": [
            "Ate all planned meals",
            "Drank at least 8 glasses of water",
            "Included fruits and vegetables",
            "Took rest if needed",
        ],
    }


def _clean_meals(items: list) -> list[dict[str, Any]]:
    cleaned: list[dict[str, Any]] = []
    for item in items[:5]:
        if isinstance(item, dict):
            cleaned.append({
                "seq": _coerce_int(item.get("seq"), len(cleaned) + 1),
                "title": _normalize_text(item.get("title")),
                "subtitle": _normalize_text(item.get("subtitle") or item.get("time")),
                "description": _normalize_text(item.get("description")),
                "duration": _normalize_text(item.get("duration") or item.get("time")),
            })
        elif isinstance(item, str) and item.strip():
            cleaned.append({
                "seq": len(cleaned) + 1,
                "title": item.strip(),
                "subtitle": "",
                "description": "",
                "duration": "",
            })
    return cleaned


def normalize_attributes(data: dict) -> dict[str, Any]:
    try:
        attrs = _safe(data, "attributes", {})
        today_focus = attrs.get("today_focus", [])
        meals_summary = attrs.get("meals_summary", {})
        if not isinstance(meals_summary, dict):
            meals_summary = {}
        normalized_focus = [
            _normalize_text(item) for item in today_focus[:4]
            if _normalize_text(item)
        ] if isinstance(today_focus, list) else []
        if not normalized_focus:
            normalized_focus = _default_today_focus()
        return {
            "calories_intake": _normalize_text(attrs.get("calories_intake"), "2000 kcal"),
            "activity": _normalize_text(attrs.get("activity"), "Moderate"),
            "goal": _normalize_text(attrs.get("goal"), "Maintenance"),
            "diet_type": _normalize_text(attrs.get("diet_type"), "Balanced"),
            "today_focus": normalized_focus,
            "posture_insight": _normalize_text(
                attrs.get("posture_insight"),
                "Consistency improves energy, digestion and overall health over time.",
            ),
            "meals_summary": {
                "total_meals": _coerce_int(meals_summary.get("total_meals"), 3),
                "total_snacks": _coerce_int(meals_summary.get("total_snacks"), 2),
                "prep_time_min": _coerce_int(meals_summary.get("prep_time_min"), 22),
            },
        }
    except Exception as e:
        logger.error(f"Error normalizing diet attributes: {e}")
        return {
            "calories_intake": "2000 kcal",
            "activity": "Moderate",
            "goal": "Maintenance",
            "diet_type": "Balanced",
            "today_focus": _default_today_focus(),
            "posture_insight": "Consistency improves energy, digestion and overall health over time.",
            "meals_summary": {"total_meals": 3, "total_snacks": 2, "prep_time_min": 22},
        }


def normalize_nutrition_targets(data: dict) -> dict[str, Any]:
    try:
        nutrition = _safe(data, "nutrition_targets", {})
        defaults = _default_nutrition_targets()
        return {
            "daily_calories": _coerce_int(nutrition.get("daily_calories"), defaults["daily_calories"]),
            "protein_g": _coerce_int(nutrition.get("protein_g"), defaults["protein_g"]),
            "carbs_g": _coerce_int(nutrition.get("carbs_g"), defaults["carbs_g"]),
            "fat_g": _coerce_int(nutrition.get("fat_g"), defaults["fat_g"]),
            "water_glasses": _coerce_int(nutrition.get("water_glasses"), defaults["water_glasses"]),
            "fiber_g": _coerce_int(nutrition.get("fiber_g"), defaults["fiber_g"]),
        }
    except Exception as e:
        logger.error(f"Error normalizing diet nutrition targets: {e}")
        return _default_nutrition_targets()


def normalize_routine(data: dict) -> dict[str, list[dict[str, Any]]]:
    try:
        routine = _safe(data, "routine", {})
        if not isinstance(routine, dict):
            return _default_routine()
        normalized = {
            "morning": _clean_meals(routine.get("morning", []) if isinstance(routine.get("morning"), list) else []),
            "evening": _clean_meals(routine.get("evening", []) if isinstance(routine.get("evening"), list) else []),
        }
        defaults = _default_routine()
        if not normalized["morning"]:
            normalized["morning"] = defaults["morning"]
        if not normalized["evening"]:
            normalized["evening"] = defaults["evening"]
        return normalized
    except Exception as e:
        logger.error(f"Error normalizing diet routine: {e}")
        return _default_routine()


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
            "daily_calories": _normalize_text(progress.get("daily_calories"), defaults["daily_calories"]),
            "consistency": _normalize_text(progress.get("consistency"), defaults["consistency"]),
            "nutrition_balance": _normalize_text(progress.get("nutrition_balance"), defaults["nutrition_balance"]),
            "diet_consistency": _normalize_text(progress.get("diet_consistency"), defaults["diet_consistency"]),
            "calorie_balance": _normalize_text(progress.get("calorie_balance"), defaults["calorie_balance"]),
            "recovery_checklist": normalized_checklist or defaults["recovery_checklist"],
        }
    except Exception as e:
        logger.error(f"Error normalizing diet progress tracking: {e}")
        return _default_progress_tracking()


def analyze_diet(answers: list[dict], images: list[dict]) -> Optional[dict[str, Any]]:
    try:
        context = build_context(answers, images)
        raw = run_gemini_json(prompt_diet_full(context), domain="diet")

        if not raw:
            logger.warning("Empty response from Gemini for diet analysis")
            return None

        return {
            "attributes": normalize_attributes(raw),
            "nutrition_targets": normalize_nutrition_targets(raw),
            "routine": normalize_routine(raw),
            "progress_tracking": normalize_progress_tracking(raw),
            "motivational_message": _normalize_text(
                raw.get("motivational_message"),
                "Small daily diet improvements create long-term healthy habits. Keep going!",
            ),
        }
    except GeminiError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in diet analysis: {e}", exc_info=True)
        return None
