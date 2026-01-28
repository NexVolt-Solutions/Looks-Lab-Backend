"""
Facial domain AI processor.
Analyzes facial features and generates personalized exercise plans.
"""
from typing import Any

from app.ai.gemini_client import run_gemini_json, GeminiError
from app.ai.facial.prompts import prompt_facial_full
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
            "symmetry": attributes.get("symmetry", "Mostly"),
            "jawline": attributes.get("jawline", "Medium"),
            "cheekbones": attributes.get("cheekbones", "Medium"),
            "habits": attributes.get("habits", "Medium"),
            "feature_goal": attributes.get("feature_goal", "Overall improvement"),
            "exercise_time": attributes.get("exercise_time", "10-15 min"),
        }
    except Exception as e:
        logger.error(f"Error normalizing facial attributes: {str(e)}")
        return {
            "symmetry": "Mostly",
            "jawline": "Medium",
            "cheekbones": "Medium",
            "habits": "Medium",
            "feature_goal": "Overall improvement",
            "exercise_time": "10-15 min",
        }


def normalize_feature_scores(data: dict) -> dict[str, str]:
    try:
        scores = _get_safe_value(data, "feature_scores", {})

        return {
            "jawline": scores.get("jawline", "75%"),
            "cheekbones": scores.get("cheekbones", "75%"),
            "symmetry": scores.get("symmetry", "75%"),
            "overall": scores.get("overall", "75%"),
            "face_shape": scores.get("face_shape", "Oval"),
        }
    except Exception as e:
        logger.error(f"Error normalizing facial feature scores: {str(e)}")
        return {
            "jawline": "75%",
            "cheekbones": "75%",
            "symmetry": "75%",
            "overall": "75%",
            "face_shape": "Oval",
        }


def normalize_daily_exercises(data: dict) -> list[dict[str, Any]]:
    try:
        exercises = _get_safe_value(data, "daily_exercises", [])

        if not isinstance(exercises, list):
            return []

        normalized = []
        for ex in exercises[:5]:
            if not isinstance(ex, dict):
                continue

            normalized.append({
                "name": ex.get("name", "Exercise"),
                "duration": ex.get("duration", "5 min"),
                "steps": ex.get("steps", []) if isinstance(ex.get("steps"), list) else []
            })

        return normalized
    except Exception as e:
        logger.error(f"Error normalizing facial exercises: {str(e)}")
        return []


def normalize_progress_tracking(data: dict) -> dict[str, Any]:
    try:
        progress = _get_safe_value(data, "progress_tracking", {})

        feature_improvement = progress.get("feature_improvement", {})
        if not isinstance(feature_improvement, dict):
            feature_improvement = {}

        checklist = progress.get("checklist", [])
        if not isinstance(checklist, list):
            checklist = []

        return {
            "consistency": progress.get("consistency", "0%"),
            "feature_improvement": {
                "jawline": feature_improvement.get("jawline", "75%"),
                "cheekbones": feature_improvement.get("cheekbones", "75%"),
                "symmetry": feature_improvement.get("symmetry", "75%"),
            },
            "checklist": checklist[:5]
        }
    except Exception as e:
        logger.error(f"Error normalizing facial progress tracking: {str(e)}")
        return {
            "consistency": "0%",
            "feature_improvement": {
                "jawline": "75%",
                "cheekbones": "75%",
                "symmetry": "75%",
            },
            "checklist": []
        }


def analyze_facial(answers: list[dict], images: list[dict]) -> dict[str, Any] | None:
    try:
        logger.info(f"Starting facial analysis with {len(answers)} answers and {len(images)} images")

        context = build_context(answers, images)
        prompt = prompt_facial_full(context)

        raw = run_gemini_json(prompt, domain="facial")

        if not raw:
            logger.warning("Empty response from Gemini for facial analysis")
            return None

        normalized = {
            "attributes": normalize_attributes(raw),
            "feature_scores": normalize_feature_scores(raw),
            "daily_exercises": normalize_daily_exercises(raw),
            "progress_tracking": normalize_progress_tracking(raw),
            "motivational_message": raw.get("motivational_message", "Keep practicing daily for best results!")
        }

        logger.info("Successfully completed facial analysis")
        return normalized

    except GeminiError as e:
        logger.error(f"Gemini AI error in facial analysis: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in facial analysis: {str(e)}", exc_info=True)
        return None

