from typing import Any, Optional

from app.ai.gemini_client import GeminiError, run_gemini_json
from app.ai.skin_care.prompts import build_context, prompt_skincare_full
from app.core.logging import logger


def _safe(data: dict, key: str, default: Any = None) -> Any:
    return data.get(key, default) if data else default


def _confidence_dict(data: dict, key: str, default_label: str = "Unknown") -> dict[str, Any]:
    if not data or key not in data:
        return {"label": default_label, "confidence": 0}
    value = data[key]
    if isinstance(value, dict):
        return {"label": value.get("label", default_label), "confidence": value.get("confidence", 0)}
    return {"label": str(value), "confidence": 0}


def normalize_attributes(data: dict) -> dict[str, dict[str, Any]]:
    try:
        attrs = _safe(data, "attributes", {})
        return {
            "skin_type":       _confidence_dict(attrs, "skin_type", "Normal"),
            "sensitivity":     _confidence_dict(attrs, "sensitivity", "Low"),
            "elasticity":      _confidence_dict(attrs, "elasticity", "Moderate"),
            "oil_balance":     _confidence_dict(attrs, "oil_balance", "Balanced"),
            "hydration":       _confidence_dict(attrs, "hydration", "Moderate"),
            "pore_visibility": _confidence_dict(attrs, "pore_visibility", "Low"),
        }
    except Exception as e:
        logger.error(f"Error normalizing skincare attributes: {e}")
        return {k: {"label": v, "confidence": 0} for k, v in {
            "skin_type": "Normal", "sensitivity": "Low", "elasticity": "Moderate",
            "oil_balance": "Balanced", "hydration": "Moderate", "pore_visibility": "Low",
        }.items()}


def normalize_health(data: dict) -> dict[str, dict[str, Any]]:
    try:
        health = _safe(data, "health", {})
        return {
            "skin_health":  _confidence_dict(health, "skin_health", "Healthy"),
            "texture":      _confidence_dict(health, "texture", "Smooth"),
            "skin_barrier": _confidence_dict(health, "skin_barrier", "Strong"),
            "smoothness":   _confidence_dict(health, "smoothness", "Smooth"),
            "brightness":   _confidence_dict(health, "brightness", "Bright"),
        }
    except Exception as e:
        logger.error(f"Error normalizing skincare health: {e}")
        return {k: {"label": v, "confidence": 0} for k, v in {
            "skin_health": "Healthy", "texture": "Smooth", "skin_barrier": "Strong",
            "smoothness": "Smooth", "brightness": "Bright",
        }.items()}


def normalize_concerns(data: dict) -> dict[str, dict[str, Any]]:
    try:
        concerns = _safe(data, "concerns", {})
        return {
            "acne_breakouts": _confidence_dict(concerns, "acne_breakouts", "None"),
            "pigmentation":   _confidence_dict(concerns, "pigmentation", "None"),
            "darkness_spot":  _confidence_dict(concerns, "darkness_spot", "None"),
            "wrinkles":       _confidence_dict(concerns, "wrinkles", "None"),
            "uneven_tone":    _confidence_dict(concerns, "uneven_tone", "None"),
        }
    except Exception as e:
        logger.error(f"Error normalizing skincare concerns: {e}")
        return {k: {"label": "None", "confidence": 0} for k in
                ["acne_breakouts", "pigmentation", "darkness_spot", "wrinkles", "uneven_tone"]}


def normalize_routine(data: dict) -> dict[str, list[dict[str, str]]]:
    try:
        routine = _safe(data, "routine", {})
        if not isinstance(routine, dict):
            return {"today": [], "night": []}

        def clean_items(items: list) -> list[dict]:
            if not isinstance(items, list):
                return []
            return [
                {"title": i.get("title", ""), "description": i.get("description", "")}
                for i in items[:5] if isinstance(i, dict)
            ]

        return {
            "today": clean_items(routine.get("today", [])),
            "night": clean_items(routine.get("night", [])),
        }
    except Exception as e:
        logger.error(f"Error normalizing skincare routine: {e}")
        return {"today": [], "night": []}


def normalize_remedies(data: dict) -> dict[str, Any]:
    try:
        remedies_raw = _safe(data, "remedies", [])
        safety_tips  = _safe(data, "safety_tips", [])

        if not isinstance(remedies_raw, list):
            return {"remedies": [], "safety_tips": []}

        remedies = []
        for i, r in enumerate(remedies_raw[:5]):
            if isinstance(r, dict):
                remedies.append({
                    "index": i + 1,
                    "name":  r.get("name", ""),
                    "steps": r.get("steps", []) if isinstance(r.get("steps"), list) else [],
                })
            elif isinstance(r, str):
                remedies.append({"index": i + 1, "name": r, "steps": []})

        return {
            "remedies":    remedies,
            "safety_tips": [str(t) for t in safety_tips if t] if isinstance(safety_tips, list) else [],
        }
    except Exception as e:
        logger.error(f"Error normalizing skincare remedies: {e}")
        return {"remedies": [], "safety_tips": []}


def normalize_products(data: dict) -> list[dict[str, Any]]:
    try:
        products = _safe(data, "products", [])
        if not isinstance(products, list):
            return []

        result = []
        for p in products[:3]:
            if not isinstance(p, dict):
                continue
            result.append({
                "name":          p.get("name", "Product"),
                "tags":          p.get("tags", []) if isinstance(p.get("tags"), list) else [],
                "time_of_day":   p.get("time_of_day", "AM/PM"),
                "overview":      p.get("overview", ""),
                "how_to_use":    p.get("how_to_use", []) if isinstance(p.get("how_to_use"), list) else [],
                "when_to_use":   p.get("when_to_use", "Daily"),
                "dont_use_with": p.get("dont_use_with", []) if isinstance(p.get("dont_use_with"), list) else [],
                "confidence":    p.get("confidence", 0),
            })
        return result
    except Exception as e:
        logger.error(f"Error normalizing skincare products: {e}")
        return []


def analyze_skincare(answers: list[dict], images: list[dict]) -> Optional[dict[str, Any]]:
    try:
        context = build_context(answers, images)
        raw = run_gemini_json(prompt_skincare_full(context), domain="skincare")

        if not raw:
            logger.warning("Empty response from Gemini for skincare analysis")
            return None

        return {
            "attributes":           normalize_attributes(raw),
            "health":               normalize_health(raw),
            "concerns":             normalize_concerns(raw),
            "routine":              normalize_routine(raw),
            "remedies":             normalize_remedies(raw),
            "products":             normalize_products(raw),
            "motivational_message": raw.get("motivational_message", "Consistency is key — your skin will thank you with a healthy glow!"),
        }
    except GeminiError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in skincare analysis: {e}", exc_info=True)
        return None

