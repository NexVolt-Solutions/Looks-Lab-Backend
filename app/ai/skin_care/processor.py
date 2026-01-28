"""
Skin care domain AI processor.
Analyzes skin health and generates personalized skincare routines.
"""
from typing import Any

from app.ai.gemini_client import run_gemini_json, GeminiError
from app.ai.skin_care.prompts import prompt_skincare_full, build_context
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
            "skin_type": _get_confidence_dict(attributes, "skin_type", "Normal"),
            "tone": _get_confidence_dict(attributes, "tone", "Medium"),
            "sensitivity": _get_confidence_dict(attributes, "sensitivity", "Low"),
            "hydration": _get_confidence_dict(attributes, "hydration", "Medium"),
        }
    except Exception as e:
        logger.error(f"Error normalizing skincare attributes: {str(e)}")
        return {
            "skin_type": {"label": "Normal", "confidence": 0},
            "tone": {"label": "Medium", "confidence": 0},
            "sensitivity": {"label": "Low", "confidence": 0},
            "hydration": {"label": "Medium", "confidence": 0},
        }


def normalize_health(data: dict) -> dict[str, dict[str, Any]]:
    try:
        health = _get_safe_value(data, "health", {})

        return {
            "acne": _get_confidence_dict(health, "acne", "None"),
            "dryness": _get_confidence_dict(health, "dryness", "None"),
            "oiliness": _get_confidence_dict(health, "oiliness", "None"),
            "redness": _get_confidence_dict(health, "redness", "None"),
        }
    except Exception as e:
        logger.error(f"Error normalizing skincare health: {str(e)}")
        return {
            "acne": {"label": "None", "confidence": 0},
            "dryness": {"label": "None", "confidence": 0},
            "oiliness": {"label": "None", "confidence": 0},
            "redness": {"label": "None", "confidence": 0},
        }


def normalize_concerns(data: dict) -> dict[str, dict[str, Any]]:
    try:
        concerns = _get_safe_value(data, "concerns", {})

        return {
            "wrinkles": _get_confidence_dict(concerns, "wrinkles", "None"),
            "pigmentation": _get_confidence_dict(concerns, "pigmentation", "None"),
            "dark_circles": _get_confidence_dict(concerns, "dark_circles", "None"),
        }
    except Exception as e:
        logger.error(f"Error normalizing skincare concerns: {str(e)}")
        return {
            "wrinkles": {"label": "None", "confidence": 0},
            "pigmentation": {"label": "None", "confidence": 0},
            "dark_circles": {"label": "None", "confidence": 0},
        }


def normalize_routine(data: dict) -> dict[str, list[dict[str, str]]]:
    try:
        routine = _get_safe_value(data, "routine", {})

        morning = routine.get("morning", [])
        night = routine.get("night", [])

        if not isinstance(morning, list):
            morning = []
        if not isinstance(night, list):
            night = []

        return {
            "morning": morning[:5],
            "night": night[:5],
        }
    except Exception as e:
        logger.error(f"Error normalizing skincare routine: {str(e)}")
        return {
            "morning": [],
            "night": [],
        }


def normalize_remedies(data: dict) -> list[str]:
    try:
        remedies = _get_safe_value(data, "remedies", [])

        if not isinstance(remedies, list):
            return []

        return [str(r) for r in remedies[:5] if r]
    except Exception as e:
        logger.error(f"Error normalizing skincare remedies: {str(e)}")
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
        logger.error(f"Error normalizing skincare products: {str(e)}")
        return []


def analyze_skincare(answers: list[dict], images: list[dict]) -> dict[str, Any] | None:
    try:
        logger.info(f"Starting skincare analysis with {len(answers)} answers and {len(images)} images")

        context = build_context(answers, images)
        prompt = prompt_skincare_full(context)

        raw = run_gemini_json(prompt, domain="skincare")

        if not raw:
            logger.warning("Empty response from Gemini for skincare analysis")
            return None

        normalized = {
            "attributes": normalize_attributes(raw),
            "health": normalize_health(raw),
            "concerns": normalize_concerns(raw),
            "routine": normalize_routine(raw),
            "remedies": normalize_remedies(raw),
            "products": normalize_products(raw),
        }

        logger.info("Successfully completed skincare analysis")
        return normalized

    except GeminiError as e:
        logger.error(f"Gemini AI error in skincare analysis: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in skincare analysis: {str(e)}", exc_info=True)
        return None

