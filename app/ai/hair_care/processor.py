"""
Hair care domain AI processor.
Analyzes hair health and generates personalized care recommendations.
"""
from typing import Any

from app.ai.gemini_client import run_gemini_json, GeminiError
from app.ai.hair_care.prompts import prompt_haircare_full, build_context
from app.core.logging import logger


def _get_safe_value(data: dict, key: str, default: Any = None) -> Any:
    return data.get(key, default) if data else default


def _get_confidence_dict(data: dict, key: str, default_label: str = "Unknown") -> dict[str, Any]:
    if not data or key not in data:
        return {"label": default_label, "confidence": 0}

    value = data[key]
    if isinstance(value, dict):
        return {
            "label": value.get("label", default_label),
            "confidence": value.get("confidence", 0)
        }

    return {"label": str(value), "confidence": 0}


def normalize_attributes(data: dict) -> dict[str, dict[str, Any]]:
    try:
        attributes = _get_safe_value(data, "attributes", {})

        return {
            "density": _get_confidence_dict(attributes, "density", "Medium"),
            "hair_type": _get_confidence_dict(attributes, "hair_type", "Straight"),
            "volume": _get_confidence_dict(attributes, "volume", "Normal"),
            "texture": _get_confidence_dict(attributes, "texture", "Medium"),
        }
    except Exception as e:
        logger.error(f"Error normalizing haircare attributes: {str(e)}")
        return {
            "density": {"label": "Medium", "confidence": 0},
            "hair_type": {"label": "Straight", "confidence": 0},
            "volume": {"label": "Normal", "confidence": 0},
            "texture": {"label": "Medium", "confidence": 0},
        }


def normalize_health(data: dict) -> dict[str, dict[str, Any]]:
    try:
        health = _get_safe_value(data, "health", {})

        return {
            "scalp_health": _get_confidence_dict(health, "scalp_health", "Healthy"),
            "breakage": _get_confidence_dict(health, "breakage", "None"),
            "frizz_dandruff": _get_confidence_dict(health, "frizz_dandruff", "None"),
            "dandruff": _get_confidence_dict(health, "dandruff", "None"),
        }
    except Exception as e:
        logger.error(f"Error normalizing haircare health: {str(e)}")
        return {
            "scalp_health": {"label": "Healthy", "confidence": 0},
            "breakage": {"label": "None", "confidence": 0},
            "frizz_dandruff": {"label": "None", "confidence": 0},
            "dandruff": {"label": "None", "confidence": 0},
        }


def normalize_concerns(data: dict) -> dict[str, dict[str, Any]]:
    try:
        concerns = _get_safe_value(data, "concerns", {})

        return {
            "hairloss": _get_confidence_dict(concerns, "hairloss", "None"),
            "hairline_recession": _get_confidence_dict(concerns, "hairline_recession", "None"),
            "stage": _get_confidence_dict(concerns, "stage", "No concerns"),
        }
    except Exception as e:
        logger.error(f"Error normalizing haircare concerns: {str(e)}")
        return {
            "hairloss": {"label": "None", "confidence": 0},
            "hairline_recession": {"label": "None", "confidence": 0},
            "stage": {"label": "No concerns", "confidence": 0},
        }


def normalize_routine(data: dict) -> dict[str, list[dict[str, str]]]:
    try:
        routine = _get_safe_value(data, "routine", {})

        today = routine.get("today", [])
        night = routine.get("night", [])

        if not isinstance(today, list):
            today = []
        if not isinstance(night, list):
            night = []

        return {
            "today": today[:5],
            "night": night[:5],
        }
    except Exception as e:
        logger.error(f"Error normalizing haircare routine: {str(e)}")
        return {
            "today": [],
            "night": [],
        }


def normalize_remedies(data: dict) -> list[str]:
    try:
        remedies = _get_safe_value(data, "remedies", [])

        if not isinstance(remedies, list):
            return []

        return [str(r) for r in remedies[:5] if r]
    except Exception as e:
        logger.error(f"Error normalizing haircare remedies: {str(e)}")
        return []


def normalize_products(data: dict) -> list[dict[str, Any]]:
    try:
        products = _get_safe_value(data, "products", [])

        if not isinstance(products, list):
            return []

        normalized = []
        for p in products[:3]:
            if not isinstance(p, dict):
                continue

            normalized.append({
                "name": p.get("name", "Product"),
                "overview": p.get("overview", ""),
                "how_to_use": p.get("how_to_use", []) if isinstance(p.get("how_to_use"), list) else [],
                "when_to_use": p.get("when_to_use", "Daily"),
                "dont_use_with": p.get("dont_use_with", []) if isinstance(p.get("dont_use_with"), list) else [],
                "confidence": p.get("confidence", 0)
            })

        return normalized
    except Exception as e:
        logger.error(f"Error normalizing haircare products: {str(e)}")
        return []


def analyze_haircare(answers: list[dict], images: list[dict]) -> dict[str, Any] | None:
    try:
        logger.info(f"Starting haircare analysis with {len(answers)} answers and {len(images)} images")

        context = build_context(answers, images)
        prompt = prompt_haircare_full(context)

        raw = run_gemini_json(prompt, domain="haircare")

        if not raw:
            logger.warning("Empty response from Gemini for haircare analysis")
            return None

        normalized = {
            "attributes": normalize_attributes(raw),
            "health": normalize_health(raw),
            "concerns": normalize_concerns(raw),
            "routine": normalize_routine(raw),
            "remedies": normalize_remedies(raw),
            "products": normalize_products(raw),
        }

        logger.info("Successfully completed haircare analysis")
        return normalized

    except GeminiError as e:
        logger.error(f"Gemini AI error in haircare analysis: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in haircare analysis: {str(e)}", exc_info=True)
        return None

