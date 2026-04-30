from typing import Any, Optional

from app.ai.gemini_client import GeminiError, run_gemini_json
from app.ai.hair_care.prompts import build_context, prompt_haircare_full
from app.core.logging import logger


def _safe(data: dict, key: str, default: Any = None) -> Any:
    return data.get(key, default) if data else default


def _normalize_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text or default


def _coerce_confidence(value: Any) -> int:
    try:
        numeric = int(float(value))
    except (TypeError, ValueError):
        return 0
    return max(0, min(100, numeric))


def _confidence_dict(data: dict, key: str, default_label: str = "Unknown") -> dict[str, Any]:
    if not data or key not in data:
        return {"label": default_label, "confidence": 0}
    value = data[key]
    if isinstance(value, dict):
        return {
            "label": _normalize_text(value.get("label"), default_label),
            "confidence": _coerce_confidence(value.get("confidence", 0)),
        }
    return {"label": _normalize_text(value, default_label), "confidence": 0}


def _default_routine() -> dict[str, list[dict[str, str]]]:
    return {
        "today": [
            {
                "title": "Gentle Scalp Wash",
                "description": "Clean away oil and buildup without over-drying the scalp.",
            },
            {
                "title": "Targeted Scalp Serum",
                "description": "Apply a lightweight scalp treatment that matches your main concern.",
            },
            {
                "title": "Five-Minute Scalp Massage",
                "description": "Massage gently to support circulation and reduce scalp tension.",
            },
        ],
        "night": [
            {
                "title": "Light Scalp Refresh",
                "description": "Keep the scalp fresh and comfortable before bed if needed.",
            },
            {
                "title": "Overnight Root Care",
                "description": "Use a soothing leave-in scalp product if dryness or irritation is present.",
            },
            {
                "title": "Protective Sleep Routine",
                "description": "Reduce friction overnight with a gentle, protective hair setup.",
            },
        ],
    }


def _default_remedies() -> dict[str, Any]:
    return {
        "remedies": [
            {"index": 1, "name": "Aloe Vera Gel", "steps": ["Use 2-3 times per week", "Helps calm the scalp and reduce dryness."]},
            {"index": 2, "name": "Green Tea Scalp Rinse", "steps": ["Use after washing hair", "Can help reduce buildup and refresh the scalp."]},
            {"index": 3, "name": "Gentle Scalp Massage", "steps": ["Massage with fingertips for a few minutes", "Supports circulation without irritating the scalp."]},
        ],
        "safety_tips": [
            "Patch test before trying a new remedy.",
            "Stop use if irritation increases.",
            "Avoid getting products into the eyes.",
        ],
    }


def normalize_attributes(data: dict) -> dict[str, dict[str, Any]]:
    try:
        attrs = _safe(data, "attributes", {})
        return {
            "density": _confidence_dict(attrs, "density", "Medium"),
            "hair_type": _confidence_dict(attrs, "hair_type", "Straight"),
            "volume": _confidence_dict(attrs, "volume", "Normal"),
            "texture": _confidence_dict(attrs, "texture", "Medium"),
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
            "breakage": _confidence_dict(health, "breakage", "None"),
            "frizz_dryness": _confidence_dict(health, "frizz_dryness", "None"),
            "dandruff": _confidence_dict(health, "dandruff", "None"),
        }
    except Exception as e:
        logger.error(f"Error normalizing haircare health: {e}")
        return {
            "scalp_health": {"label": "Healthy", "confidence": 0},
            "breakage": {"label": "None", "confidence": 0},
            "frizz_dryness": {"label": "None", "confidence": 0},
            "dandruff": {"label": "None", "confidence": 0},
        }


def normalize_concerns(data: dict) -> dict[str, dict[str, Any]]:
    try:
        concerns = _safe(data, "concerns", {})
        return {
            "hairloss": _confidence_dict(concerns, "hairloss", "None"),
            "hairline_recession": _confidence_dict(concerns, "hairline_recession", "None"),
            "stage": _confidence_dict(concerns, "stage", "No concerns"),
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
            return _default_routine()

        def clean_items(items: list) -> list[dict[str, str]]:
            if not isinstance(items, list):
                return []
            cleaned = []
            for item in items[:5]:
                if not isinstance(item, dict):
                    continue
                title = _normalize_text(item.get("title"))
                description = _normalize_text(item.get("description"))
                if title or description:
                    cleaned.append({"title": title, "description": description})
            return cleaned

        normalized = {
            "today": clean_items(routine.get("today", [])),
            "night": clean_items(routine.get("night", [])),
        }
        defaults = _default_routine()
        if not normalized["today"]:
            normalized["today"] = defaults["today"]
        if not normalized["night"]:
            normalized["night"] = defaults["night"]
        return normalized
    except Exception as e:
        logger.error(f"Error normalizing haircare routine: {e}")
        return _default_routine()


def normalize_remedies(data: dict) -> dict[str, Any]:
    try:
        remedies_raw = _safe(data, "remedies", [])
        safety_tips = _safe(data, "safety_tips", [])

        if not isinstance(remedies_raw, list):
            return _default_remedies()

        remedies = []
        for i, remedy in enumerate(remedies_raw[:5]):
            if isinstance(remedy, dict):
                remedies.append({
                    "index": i + 1,
                    "name": _normalize_text(remedy.get("name"), f"Remedy {i + 1}"),
                    "steps": [
                        _normalize_text(step) for step in remedy.get("steps", [])
                        if _normalize_text(step)
                    ] if isinstance(remedy.get("steps"), list) else [],
                })
            elif isinstance(remedy, str) and remedy.strip():
                remedies.append({"index": i + 1, "name": remedy.strip(), "steps": []})

        normalized_tips = [
            _normalize_text(tip) for tip in safety_tips
            if _normalize_text(tip)
        ] if isinstance(safety_tips, list) else []

        normalized = {
            "remedies": remedies,
            "safety_tips": normalized_tips,
        }
        defaults = _default_remedies()
        if not normalized["remedies"]:
            normalized["remedies"] = defaults["remedies"]
        if not normalized["safety_tips"]:
            normalized["safety_tips"] = defaults["safety_tips"]
        return normalized
    except Exception as e:
        logger.error(f"Error normalizing haircare remedies: {e}")
        return _default_remedies()


def normalize_products(data: dict) -> list[dict[str, Any]]:
    try:
        products = _safe(data, "products", [])
        if not isinstance(products, list):
            return []

        result = []
        for product in products[:3]:
            if not isinstance(product, dict):
                continue
            result.append({
                "name": _normalize_text(product.get("name"), "Product"),
                "tags": [
                    _normalize_text(tag) for tag in product.get("tags", [])
                    if _normalize_text(tag)
                ] if isinstance(product.get("tags"), list) else [],
                "time_of_day": _normalize_text(product.get("time_of_day"), "AM/PM"),
                "overview": _normalize_text(product.get("overview")),
                "how_to_use": [
                    _normalize_text(step) for step in product.get("how_to_use", [])
                    if _normalize_text(step)
                ] if isinstance(product.get("how_to_use"), list) else [],
                "when_to_use": _normalize_text(product.get("when_to_use"), "Daily"),
                "dont_use_with": [
                    _normalize_text(item) for item in product.get("dont_use_with", [])
                    if _normalize_text(item)
                ] if isinstance(product.get("dont_use_with"), list) else [],
                "confidence": _coerce_confidence(product.get("confidence", 0)),
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
            "attributes": normalize_attributes(raw),
            "health": normalize_health(raw),
            "concerns": normalize_concerns(raw),
            "routine": normalize_routine(raw),
            "remedies": normalize_remedies(raw),
            "products": normalize_products(raw),
            "motivational_message": _normalize_text(
                raw.get("motivational_message"),
                "Consistency is key - your scalp health can improve with steady daily care.",
            ),
        }
    except GeminiError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in haircare analysis: {e}", exc_info=True)
        return None
