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


def _get_confidence_dict(
    data: dict,
    key: str,
    default_label: str = "Unknown"
) -> dict[str, Any]:
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
    """
    Matches Figma: Skin Type, Sensitivity, Elasticity,
    Oil Balance, Hydration, Pore Visibility
    """
    try:
        attributes = _get_safe_value(data, "attributes", {})

        return {
            "skin_type": _get_confidence_dict(attributes, "skin_type", "Normal"),
            "sensitivity": _get_confidence_dict(attributes, "sensitivity", "Low"),
            "elasticity": _get_confidence_dict(attributes, "elasticity", "Moderate"),
            "oil_balance": _get_confidence_dict(attributes, "oil_balance", "Balanced"),
            "hydration": _get_confidence_dict(attributes, "hydration", "Moderate"),
            "pore_visibility": _get_confidence_dict(attributes, "pore_visibility", "Low"),
        }
    except Exception as e:
        logger.error(f"Error normalizing skincare attributes: {str(e)}")
        return {
            "skin_type": {"label": "Normal", "confidence": 0},
            "sensitivity": {"label": "Low", "confidence": 0},
            "elasticity": {"label": "Moderate", "confidence": 0},
            "oil_balance": {"label": "Balanced", "confidence": 0},
            "hydration": {"label": "Moderate", "confidence": 0},
            "pore_visibility": {"label": "Low", "confidence": 0},
        }


def normalize_health(data: dict) -> dict[str, dict[str, Any]]:
    """
    Matches Figma: Skin Health, Texture, Skin Barrier,
    Smoothness, Brightness
    """
    try:
        health = _get_safe_value(data, "health", {})

        return {
            "skin_health": _get_confidence_dict(health, "skin_health", "Healthy"),
            "texture": _get_confidence_dict(health, "texture", "Smooth"),
            "skin_barrier": _get_confidence_dict(health, "skin_barrier", "Strong"),
            "smoothness": _get_confidence_dict(health, "smoothness", "Smooth"),
            "brightness": _get_confidence_dict(health, "brightness", "Bright"),
        }
    except Exception as e:
        logger.error(f"Error normalizing skincare health: {str(e)}")
        return {
            "skin_health": {"label": "Healthy", "confidence": 0},
            "texture": {"label": "Smooth", "confidence": 0},
            "skin_barrier": {"label": "Strong", "confidence": 0},
            "smoothness": {"label": "Smooth", "confidence": 0},
            "brightness": {"label": "Bright", "confidence": 0},
        }


def normalize_concerns(data: dict) -> dict[str, dict[str, Any]]:
    """
    Matches Figma: Acne/Breakouts, Pigmentation,
    Darkness Spot, Wrinkles, Uneven Tone
    """
    try:
        concerns = _get_safe_value(data, "concerns", {})

        return {
            "acne_breakouts": _get_confidence_dict(concerns, "acne_breakouts", "None"),
            "pigmentation": _get_confidence_dict(concerns, "pigmentation", "None"),
            "darkness_spot": _get_confidence_dict(concerns, "darkness_spot", "None"),
            "wrinkles": _get_confidence_dict(concerns, "wrinkles", "None"),
            "uneven_tone": _get_confidence_dict(concerns, "uneven_tone", "None"),
        }
    except Exception as e:
        logger.error(f"Error normalizing skincare concerns: {str(e)}")
        return {
            "acne_breakouts": {"label": "None", "confidence": 0},
            "pigmentation": {"label": "None", "confidence": 0},
            "darkness_spot": {"label": "None", "confidence": 0},
            "wrinkles": {"label": "None", "confidence": 0},
            "uneven_tone": {"label": "None", "confidence": 0},
        }


def normalize_routine(data: dict) -> dict[str, list[dict[str, str]]]:
    """
    Matches Figma: Today's Routine + Night's Routine
    Each item has title + description
    """
    try:
        routine = _get_safe_value(data, "routine", {})

        today = routine.get("today", [])
        night = routine.get("night", [])

        if not isinstance(today, list):
            today = []
        if not isinstance(night, list):
            night = []

        def clean_items(items: list) -> list[dict]:
            cleaned = []
            for item in items[:5]:
                if isinstance(item, dict):
                    cleaned.append({
                        "title": item.get("title", ""),
                        "description": item.get("description", "")
                    })
            return cleaned

        return {
            "today": clean_items(today),
            "night": clean_items(night),
        }
    except Exception as e:
        logger.error(f"Error normalizing skincare routine: {str(e)}")
        return {"today": [], "night": []}


def normalize_remedies(data: dict) -> dict[str, Any]:
    """
    Matches Figma: Skin Home Remedies screen
    Structured remedies with steps + safety tips
    """
    try:
        remedies_raw = _get_safe_value(data, "remedies", [])
        safety_tips = _get_safe_value(data, "safety_tips", [])

        if not isinstance(remedies_raw, list):
            return {"remedies": [], "safety_tips": []}

        remedies = []
        for i, r in enumerate(remedies_raw[:5]):
            if isinstance(r, dict):
                remedies.append({
                    "index": i + 1,
                    "name": r.get("name", ""),
                    "steps": r.get("steps", []) if isinstance(r.get("steps"), list) else []
                })
            elif isinstance(r, str):
                # Fallback for plain string
                remedies.append({
                    "index": i + 1,
                    "name": r,
                    "steps": []
                })

        return {
            "remedies": remedies,
            "safety_tips": [str(tip) for tip in safety_tips if tip]
        }
    except Exception as e:
        logger.error(f"Error normalizing skincare remedies: {str(e)}")
        return {"remedies": [], "safety_tips": []}


def normalize_products(data: dict) -> list[dict[str, Any]]:
    """
    Matches Figma: Recommended Products screen
    Includes tags, time_of_day, dont_use_with as chips
    """
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
                "tags": p.get("tags", []) if isinstance(p.get("tags"), list) else [],
                "time_of_day": p.get("time_of_day", "AM/PM"),
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
        logger.info(
            f"Starting skincare analysis with {len(answers)} answers "
            f"and {len(images)} images"
        )

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
            "motivational_message": raw.get(
                "motivational_message",
                "Consistency is key — your skin will thank you with a healthy glow!"
            )
        }

        logger.info("Successfully completed skincare analysis")
        return normalized

    except GeminiError as e:
        logger.error(f"Gemini AI error in skincare analysis: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in skincare analysis: {str(e)}", exc_info=True)
        return None

