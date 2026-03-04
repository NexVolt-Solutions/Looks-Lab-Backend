from typing import Any, Optional

from app.ai.gemini_client import GeminiError, run_gemini_json
from app.ai.fashion.prompts import build_context, prompt_fashion_full
from app.core.logging import logger


def _safe(data: dict, key: str, default: Any = None) -> Any:
    return data.get(key, default) if data else default


def normalize_attributes(data: dict) -> dict[str, Any]:
    try:
        attrs = _safe(data, "attributes", {})
        return {
            "body_type":           attrs.get("body_type", "Athletic"),
            "undertone":           attrs.get("undertone", "Warm"),
            "style":               attrs.get("style", "Classic"),
            "best_clothing_fits":  attrs.get("best_clothing_fits", [])[:5] if isinstance(attrs.get("best_clothing_fits"), list) else [],
            "styles_to_avoid":     attrs.get("styles_to_avoid", [])[:5] if isinstance(attrs.get("styles_to_avoid"), list) else [],
            "warm_palette":        attrs.get("warm_palette", [])[:6] if isinstance(attrs.get("warm_palette"), list) else [],
            "analyzing_insights":  attrs.get("analyzing_insights", [])[:5] if isinstance(attrs.get("analyzing_insights"), list) else [],
        }
    except Exception as e:
        logger.error(f"Error normalizing fashion attributes: {e}")
        return {
            "body_type": "Athletic", "undertone": "Warm", "style": "Classic",
            "best_clothing_fits": [], "styles_to_avoid": [],
            "warm_palette": [], "analyzing_insights": [],
        }


def normalize_weekly_plan(data: dict) -> list[dict[str, str]]:
    try:
        weekly_plan = _safe(data, "weekly_plan", [])

        if isinstance(weekly_plan, dict):
            days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            weekly_plan = [{"day": day, "theme": weekly_plan.get(day, "Casual")} for day in days_order]
        elif not isinstance(weekly_plan, list):
            return []

        return [
            {"day": i.get("day", ""), "theme": i.get("theme", "Casual")}
            for i in weekly_plan[:7] if isinstance(i, dict)
        ]
    except Exception as e:
        logger.error(f"Error normalizing fashion weekly plan: {e}")
        return []


def normalize_seasonal_style(data: dict) -> dict[str, dict[str, list]]:
    _empty = {"outfit_combinations": [], "recommended_fabrics": [], "footwear": []}
    try:
        seasonal = _safe(data, "seasonal_style", {})
        result = {}
        for season in ["summer", "monsoon", "winter"]:
            s = seasonal.get(season, {}) if isinstance(seasonal, dict) else {}
            result[season] = {
                "outfit_combinations": s.get("outfit_combinations", [])[:5] if isinstance(s.get("outfit_combinations"), list) else [],
                "recommended_fabrics": s.get("recommended_fabrics", [])[:5] if isinstance(s.get("recommended_fabrics"), list) else [],
                "footwear":            s.get("footwear", [])[:5] if isinstance(s.get("footwear"), list) else [],
            }
        return result
    except Exception as e:
        logger.error(f"Error normalizing fashion seasonal style: {e}")
        return {"summer": dict(_empty), "monsoon": dict(_empty), "winter": dict(_empty)}


def analyze_fashion(answers: list[dict], images: list[dict]) -> Optional[dict[str, Any]]:
    try:
        context = build_context(answers, images)
        raw = run_gemini_json(prompt_fashion_full(context), domain="fashion")

        if not raw:
            logger.warning("Empty response from Gemini for fashion analysis")
            return None

        return {
            "attributes": normalize_attributes(raw),
            "routine": {
                "weekly_plan":    normalize_weekly_plan(raw),
                "seasonal_style": normalize_seasonal_style(raw),
            },
            "motivational_message": raw.get("motivational_message", "Your style is your identity. Own it with confidence every day!"),
        }
    except GeminiError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in fashion analysis: {e}", exc_info=True)
        return None

