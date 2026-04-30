import re
from typing import Any, Optional

from app.ai.fashion.prompts import build_context, prompt_fashion_full
from app.ai.gemini_client import GeminiError, run_gemini_json
from app.core.logging import logger

_HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")


def _safe(data: dict, key: str, default: Any = None) -> Any:
    return data.get(key, default) if data else default


def _normalize_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text or default


def _default_attributes() -> dict[str, Any]:
    return {
        "body_type": "Athletic",
        "undertone": "Warm",
        "style": "Classic",
        "best_clothing_fits": ["Fitted shirts", "Tapered pants", "Structured blazers"],
        "styles_to_avoid": ["Oversized fits", "Wide-leg pants", "Bulky layers"],
        "warm_palette": ["#C8A882", "#8B7355", "#C0622F", "#4A6741", "#C8973C", "#A0522D"],
        "analyzing_insights": [
            "Athletic body structure",
            "Warm skin undertone",
            "Balanced proportions",
            "Best fit: Regular",
            "Strong everyday style",
        ],
    }


def _default_weekly_plan() -> list[dict[str, str]]:
    return [
        {"day": "Monday", "theme": "Smart Casual"},
        {"day": "Tuesday", "theme": "Minimal"},
        {"day": "Wednesday", "theme": "Classic"},
        {"day": "Thursday", "theme": "Street"},
        {"day": "Friday", "theme": "Relaxed"},
        {"day": "Saturday", "theme": "Casual"},
        {"day": "Sunday", "theme": "Loungewear"},
    ]


def _default_seasonal_style() -> dict[str, dict[str, list[str]]]:
    return {
        "summer": {
            "outfit_combinations": ["Linen shirt", "Tailored shorts", "Lightweight sneakers"],
            "recommended_fabrics": ["Linen", "Cotton", "Chambray"],
            "footwear": ["Loafers", "Canvas sneakers", "Sandals"],
        },
        "monsoon": {
            "outfit_combinations": ["Quick-dry shirt", "Tapered pants", "Light jacket"],
            "recommended_fabrics": ["Polyester blend", "Quick-dry cotton", "Nylon"],
            "footwear": ["Waterproof boots", "Slip-on sneakers", "Floaters"],
        },
        "winter": {
            "outfit_combinations": ["Wool sweater", "Corduroy pants", "Layered blazer"],
            "recommended_fabrics": ["Wool", "Cashmere", "Flannel"],
            "footwear": ["Chelsea boots", "Derby shoes", "Suede loafers"],
        },
    }


def normalize_attributes(data: dict) -> dict[str, Any]:
    try:
        attrs = _safe(data, "attributes", {})
        defaults = _default_attributes()
        fits = attrs.get("best_clothing_fits", [])
        avoid = attrs.get("styles_to_avoid", [])
        palette = attrs.get("warm_palette", [])
        insights = attrs.get("analyzing_insights", [])
        normalized_palette = [
            color for color in [str(item).strip() for item in palette[:6]]
            if _HEX_RE.match(color)
        ] if isinstance(palette, list) else []
        return {
            "body_type": _normalize_text(attrs.get("body_type"), defaults["body_type"]),
            "undertone": _normalize_text(attrs.get("undertone"), defaults["undertone"]),
            "style": _normalize_text(attrs.get("style"), defaults["style"]),
            "best_clothing_fits": [
                _normalize_text(item) for item in fits[:5]
                if _normalize_text(item)
            ] if isinstance(fits, list) else defaults["best_clothing_fits"],
            "styles_to_avoid": [
                _normalize_text(item) for item in avoid[:5]
                if _normalize_text(item)
            ] if isinstance(avoid, list) else defaults["styles_to_avoid"],
            "warm_palette": normalized_palette or defaults["warm_palette"],
            "analyzing_insights": [
                _normalize_text(item) for item in insights[:5]
                if _normalize_text(item)
            ] if isinstance(insights, list) and any(_normalize_text(item) for item in insights[:5]) else defaults["analyzing_insights"],
        }
    except Exception as e:
        logger.error(f"Error normalizing fashion attributes: {e}")
        return _default_attributes()


def normalize_weekly_plan(data: dict) -> list[dict[str, str]]:
    try:
        weekly_plan = _safe(data, "weekly_plan", [])
        if isinstance(weekly_plan, dict):
            days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            weekly_plan = [{"day": day, "theme": weekly_plan.get(day, "Casual")} for day in days_order]
        elif not isinstance(weekly_plan, list):
            return _default_weekly_plan()

        cleaned = [
            {"day": _normalize_text(item.get("day")), "theme": _normalize_text(item.get("theme"), "Casual")}
            for item in weekly_plan[:7] if isinstance(item, dict) and (_normalize_text(item.get("day")) or _normalize_text(item.get("theme")))
        ]
        return cleaned or _default_weekly_plan()
    except Exception as e:
        logger.error(f"Error normalizing fashion weekly plan: {e}")
        return _default_weekly_plan()


def normalize_seasonal_style(data: dict) -> dict[str, dict[str, list[str]]]:
    try:
        seasonal = _safe(data, "seasonal_style", {})
        defaults = _default_seasonal_style()
        result = {}
        for season in ["summer", "monsoon", "winter"]:
            source = seasonal.get(season, {}) if isinstance(seasonal, dict) else {}
            if not isinstance(source, dict):
                source = {}
            result[season] = {
                "outfit_combinations": [
                    _normalize_text(item) for item in source.get("outfit_combinations", [])[:5]
                    if _normalize_text(item)
                ] if isinstance(source.get("outfit_combinations"), list) else defaults[season]["outfit_combinations"],
                "recommended_fabrics": [
                    _normalize_text(item) for item in source.get("recommended_fabrics", [])[:5]
                    if _normalize_text(item)
                ] if isinstance(source.get("recommended_fabrics"), list) else defaults[season]["recommended_fabrics"],
                "footwear": [
                    _normalize_text(item) for item in source.get("footwear", [])[:5]
                    if _normalize_text(item)
                ] if isinstance(source.get("footwear"), list) else defaults[season]["footwear"],
            }
            for key in ["outfit_combinations", "recommended_fabrics", "footwear"]:
                if not result[season][key]:
                    result[season][key] = defaults[season][key]
        return result
    except Exception as e:
        logger.error(f"Error normalizing fashion seasonal style: {e}")
        return _default_seasonal_style()


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
                "weekly_plan": normalize_weekly_plan(raw),
                "seasonal_style": normalize_seasonal_style(raw),
            },
            "motivational_message": _normalize_text(
                raw.get("motivational_message"),
                "Your style is your identity. Own it with confidence every day!",
            ),
        }
    except GeminiError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in fashion analysis: {e}", exc_info=True)
        return None
