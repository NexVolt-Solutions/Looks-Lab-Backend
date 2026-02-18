"""
Height domain AI processor.
Analyzes posture and generates height improvement plans.
"""
from typing import Any

from app.ai.gemini_client import run_gemini_json, GeminiError
from app.ai.height.prompts import prompt_height_full, build_context
from app.core.logging import logger


def _get_safe_value(data: dict, key: str, default: Any = None) -> Any:
    return data.get(key, default) if data else default


def normalize_attributes(data: dict) -> dict[str, str]:
    """
    Matches Figma Height screen:
    Current Height, Goal Height, BMI Status,
    Growth Potential, Posture Status
    """
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


def normalize_progress_tracking(data: dict) -> dict[str, str]:
    """
    Matches Figma Height screen:
    Progress bar %, posture gain cm, consistency %
    """
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


def normalize_today_focus(data: dict) -> list[dict[str, str]]:
    """
    Matches Figma Height screen:
    Today's Focus section showing 2 highlighted exercises
    """
    try:
        today_focus = _get_safe_value(data, "today_focus", [])

        if not isinstance(today_focus, list):
            return []

        focus = []
        for item in today_focus[:2]:  # Max 2 focus items
            if isinstance(item, dict):
                focus.append({
                    "title": item.get("title", ""),
                    "duration": item.get("duration", "5 min exercise")
                })

        return focus
    except Exception as e:
        logger.error(f"Error normalizing height today focus: {str(e)}")
        return []


def normalize_exercises(data: dict) -> dict[str, list[dict[str, Any]]]:
    """
    Matches Figma Daily Routine screen:
    Morning + Evening exercises with expandable steps
    Each exercise: seq, title, duration, steps[]
    """
    try:
        exercises = _get_safe_value(data, "exercises", {})

        morning = exercises.get("morning", [])
        evening = exercises.get("evening", [])

        if not isinstance(morning, list):
            morning = []
        if not isinstance(evening, list):
            evening = []

        def clean_exercises(items: list) -> list[dict]:
            cleaned = []
            for item in items[:5]:
                if isinstance(item, dict):
                    steps = item.get("steps", [])
                    cleaned.append({
                        "seq": item.get("seq", len(cleaned) + 1),
                        "title": item.get("title", ""),
                        "duration": item.get("duration", "5 min"),
                        "steps": [str(s) for s in steps if s] if isinstance(steps, list) else []
                    })
                elif isinstance(item, str):
                    # Fallback for plain string format
                    parts = item.split(" — ")
                    cleaned.append({
                        "seq": len(cleaned) + 1,
                        "title": parts[0].strip() if parts else item,
                        "duration": parts[1].strip() if len(parts) > 1 else "5 min",
                        "steps": []
                    })
            return cleaned

        return {
            "morning": clean_exercises(morning),
            "evening": clean_exercises(evening),
        }
    except Exception as e:
        logger.error(f"Error normalizing height exercises: {str(e)}")
        return {"morning": [], "evening": []}


def analyze_height(answers: list[dict], images: list[dict]) -> dict[str, Any] | None:
    try:
        logger.info(
            f"Starting height analysis with {len(answers)} answers "
            f"and {len(images)} images"
        )

        context = build_context(answers, images)
        prompt = prompt_height_full(context)

        raw = run_gemini_json(prompt, domain="height")

        if not raw:
            logger.warning("Empty response from Gemini for height analysis")
            return None

        normalized = {
            "attributes": normalize_attributes(raw),
            "progress_tracking": normalize_progress_tracking(raw),
            "today_focus": normalize_today_focus(raw),
            "daily_exercises": normalize_exercises(raw),
            "motivational_message": raw.get(
                "motivational_message",
                "Good posture can instantly improve your height appearance by up to 2-3 cm. Keep stretching daily!"
            )
        }

        logger.info("Successfully completed height analysis")
        return normalized

    except GeminiError as e:
        logger.error(f"Gemini AI error in height analysis: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in height analysis: {str(e)}", exc_info=True)
        return None

