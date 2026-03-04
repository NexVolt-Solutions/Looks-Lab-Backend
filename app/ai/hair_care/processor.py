from typing import Any, Optional

from app.ai.gemini_client import GeminiError, run_gemini_json
from app.ai.hair_care.prompts import build_context, prompt_haircare_full
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
            "density":   _confidence_dict(attrs, "density", "Medium"),
            "hair_type": _confidence_dict(attrs, "hair_type", "Straight"),
            "volume":    _confidence_dict(attrs, "volume", "Normal"),
            "texture":   _confidence_dict(attrs, "texture", "Medium"),
        }
    except Exception as e:
        logger.error(f"Error normalizing haircare attributes: {e}")
        return {k: {"label": v, "confidence": 0} for k, v in {
            "density": "Medium", "hair_type": "Straight", "volume": "Normal", "texture": "Medium",
        }.items()}


def normalize_health(data: dict) -> dict[str, dict[str, Any]]:
    try:
        health = _safe(data, "health", {})
        return {
            "scalp_health": _confidence_dict(health, "scalp_health", "Healthy"),
            "breakage":     _confidence_dict(health, "breakage", "None"),
            "frizz_dryness": _confidence_dict(health, "frizz_dryness", "None"),
            "dandruff":     _confidence_dict(health, "dandruff", "None"),
        }
    except Exception as e:
        logger.error(f"Error normalizing haircare health: {e}")
        return {k: {"label": "None", "confidence": 0} for k in ["scalp_health", "breakage", "frizz_dryness", "dandruff"]}


def normalize_concerns(data: dict) -> dict[str, dict[str, Any]]:
    try:
        concerns = _safe(data, "concerns", {})
        return {
            "hairloss":            _confidence_dict(concerns, "hairloss", "None"),
            "hairline_recession":  _confidence_dict(concerns, "hairline_recession", "None"),
            "stage":               _confidence_dict(concerns, "stage", "No concerns"),
        }
    except Exception as e:
        logger.error(f"Error normalizing haircare concerns: {e}")
        return {k: {"label": v, "confidence": 0} for k, v in {
            "hairloss": "None", "hairline_recession": "None", "stage": "No concerns",
        }.items()}


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
        logger.error(f"Error normalizing haircare routine: {e}")
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
        logger.error(f"Error normalizing haircare remedies: {e}")
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
        logger.error(f"Error normalizing haircare products: {e}")
        return []


def analyze_haircare(answers: list[dict], images: list[dict]) -> Optional[dict[str, Any]]:
    try:
        context = build_context(answers, images)
        raw = run_gemini_json(prompt_haircare_full(context), domain="haircare")

        if not raw:
            logger.warning("Empty response from Gemini for haircare analysis")
            return None

        return {
            "attributes":           normalize_attributes(raw),
            "health":               normalize_health(raw),
            "concerns":             normalize_concerns(raw),
            "routine":              normalize_routine(raw),
            "remedies":             normalize_remedies(raw),
            "products":             normalize_products(raw),
            "motivational_message": raw.get("motivational_message", "Consistency is key — your scalp health will improve with daily care!"),
        }
    except GeminiError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in haircare analysis: {e}", exc_info=True)
        return None

