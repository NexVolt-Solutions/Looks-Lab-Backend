"""
Height domain AI processor.
Analyzes posture and generates height improvement plans.
"""
from typing import Any

from app.ai.gemini_client import run_gemini_json, GeminiError
from app.ai.height.prompts import prompt_height_full
from app.core.logging import logger


def build_context(answers: list[dict], images: list[dict]) -> dict:
    return {
        "answers": [
            {
                "step": a.get("step"),
                "question": a.get("question"),
                "answer": a.get("answer")
            }
            for a in answers
        ],
        "images": [
            {
                "view": i.get("view"),
                "present": bool(i.get("url"))
            }
            for i in images
        ],
    }


def _get_safe_value(data: dict, key: str, default: Any = None) -> Any:
    return data.get(key, default) if data else default


def normalize_attributes(data: dict) -> dict[str, str]:
    try:
        attributes = _get_safe_value(data, "attributes", {})

        return {
            "current_height": attributes.get("current_height", "170 cm"),
            "goal_height": attributes.get("goal_height", "175 cm"),
            "growth_potential": attributes.get("growth_potential", "Moderate"),
            "posture_status": attributes.get("posture_status", "Average"),
            "bmi_status": attributes.get("bmi_status", "Normal"),
        }
    except Exception as e:
        logger.error(f"Error normalizing height attributes: {str(e)}")
        return {
            "current_height": "170 cm",
            "goal_height": "175 cm",
            "growth_potential": "Moderate",
            "posture_status": "Average",
            "bmi_status": "Normal",
        }


def normalize_routine(data: dict) -> dict[str, list[str]]:
    try:
        routine = _get_safe_value(data, "routine", {})

        morning = routine.get("morning", [])
        evening = routine.get("evening", [])

        if not isinstance(morning, list):
            morning = []
        if not isinstance(evening, list):
            evening = []

        return {
            "morning": morning[:5],
            "evening": evening[:5],
        }
    except Exception as e:
        logger.error(f"Error normalizing height routine: {str(e)}")
        return {
            "morning": [],
            "evening": [],
        }


def normalize_progress_tracking(data: dict) -> dict[str, str]:
    try:
        progress = _get_safe_value(data, "progress_tracking", {})

        return {
            "completion_percent": progress.get("completion_percent", "0%"),
            "posture_gain_cm": progress.get("posture_gain_cm", "0 cm"),
            "consistency": progress.get("consistency", "0%"),
        }
    except Exception as e:
        logger.error(f"Error normalizing height progress tracking: {str(e)}")
        return {
            "completion_percent": "0%",
            "posture_gain_cm": "0 cm",
            "consistency": "0%",
        }


def analyze_height(answers: list[dict], images: list[dict]) -> dict[str, Any] | None:
    try:
        logger.info(f"Starting height analysis with {len(answers)} answers and {len(images)} images")

        context = build_context(answers, images)
        prompt = prompt_height_full(context)

        raw = run_gemini_json(prompt, domain="height")

        if not raw:
            logger.warning("Empty response from Gemini for height analysis")
            return None

        normalized = {
            "attributes": normalize_attributes(raw),
            "routine": normalize_routine(raw),
            "progress_tracking": normalize_progress_tracking(raw),
            "motivational_message": raw.get("motivational_message", "Good posture can improve your height appearance!")
        }

        logger.info("Successfully completed height analysis")
        return normalized

    except GeminiError as e:
        logger.error(f"Gemini AI error in height analysis: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in height analysis: {str(e)}", exc_info=True)
        return None

