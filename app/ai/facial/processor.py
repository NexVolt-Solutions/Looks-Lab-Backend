"""
Facial domain AI processor.
Analyzes facial features and generates personalized exercise plans.
"""
from typing import Any

from app.ai.gemini_client import run_gemini_json, GeminiError
from app.ai.facial.prompts import prompt_facial_full, build_context
from app.core.logging import logger


def _get_safe_value(data: dict, key: str, default: Any = None) -> Any:
    return data.get(key, default) if data else default


def normalize_attributes(data: dict) -> dict[str, str]:
    """
    Matches Figma questionnaire screens:
    Symmetry, Jawline, Cheekbones, Habits, Goal, Time
    """
    try:
        attributes = _get_safe_value(data, "attributes", {})

        return {
            "symmetry": attributes.get("symmetry", "Mostly"),
            "jawline": attributes.get("jawline", "Medium/Slightly Defined"),
            "cheekbones": attributes.get("cheekbones", "Medium/Normal"),
            "habits": attributes.get("habits", "Medium/Normal"),
            "feature_goal": attributes.get("feature_goal", "Overall improvement"),
            "exercise_time": attributes.get("exercise_time", "10-15 minutes"),
        }
    except Exception as e:
        logger.error(f"Error normalizing facial attributes: {str(e)}")
        return {
            "symmetry": "Mostly",
            "jawline": "Medium/Slightly Defined",
            "cheekbones": "Medium/Normal",
            "habits": "Medium/Normal",
            "feature_goal": "Overall improvement",
            "exercise_time": "10-15 minutes",
        }


def normalize_feature_scores(data: dict) -> dict[str, Any]:
    """
    Matches Figma Your Style Profile screen:
    Overall Score + 7 feature scores with labels
    (Jawline, Nose, Lips, Cheekbones, Eyes, Ears, Face Shape)
    """
    try:
        scores = _get_safe_value(data, "feature_scores", {})

        overall_score = scores.get("overall_score", 50)
        features_raw = scores.get("features", [])

        if not isinstance(features_raw, list):
            features_raw = []


        features = []
        for f in features_raw:
            if isinstance(f, dict):
                features.append({
                    "name": f.get("name", ""),
                    "label": f.get("label", ""),
                    "score": f.get("score", 0)
                })


        if not features:
            features = [
                {"name": "Jawline", "label": "Narrow", "score": 75},
                {"name": "Nose", "label": "Straight", "score": 75},
                {"name": "Lips", "label": "Medium", "score": 75},
                {"name": "Cheek bones", "label": "High", "score": 75},
                {"name": "Eyes", "label": "Almond", "score": 75},
                {"name": "Ears", "label": "Proportional", "score": 75},
                {"name": "Face Shape", "label": "Diamond Face Shape", "score": 75},
            ]

        return {
            "overall_score": overall_score,
            "features": features
        }
    except Exception as e:
        logger.error(f"Error normalizing facial feature scores: {str(e)}")
        return {
            "overall_score": 50,
            "features": []
        }


def normalize_daily_exercises(data: dict) -> dict[str, Any]:
    """
    Matches Figma Personalized Exercise screen:
    Today's Progress count + exercises list
    Each exercise: seq, title, duration, steps[]
    """
    try:
        exercises_raw = _get_safe_value(data, "daily_exercises", [])

        if not isinstance(exercises_raw, list):
            return {"total": 0, "exercises": []}

        exercises = []
        for item in exercises_raw[:5]:
            if isinstance(item, dict):
                steps = item.get("steps", [])
                exercises.append({
                    "seq": item.get("seq", len(exercises) + 1),
                    "title": item.get("title", item.get("name", "Exercise")),
                    "duration": item.get("duration", "5 min"),
                    "steps": [str(s) for s in steps if s] if isinstance(steps, list) else []
                })

        return {
            "total": len(exercises),
            "exercises": exercises
        }
    except Exception as e:
        logger.error(f"Error normalizing facial exercises: {str(e)}")
        return {"total": 0, "exercises": []}


def normalize_progress_tracking(data: dict) -> dict[str, Any]:
    """
    Matches Figma Your Progress screen:
    Jawline %, Cheekbones %, Symmetry %,
    Consistency %, Recovery Checklist
    """
    try:
        progress = _get_safe_value(data, "progress_tracking", {})

        checklist = progress.get("recovery_checklist", [])
        if not isinstance(checklist, list):
            checklist = []

        return {
            "jawline_score": progress.get("jawline_score", 78),
            "cheekbones_score": progress.get("cheekbones_score", 72),
            "symmetry_score": progress.get("symmetry_score", 75),
            "consistency": progress.get("consistency", "0%"),
            "recovery_checklist": [
                str(item) for item in checklist[:3] if item
            ]
        }
    except Exception as e:
        logger.error(f"Error normalizing facial progress tracking: {str(e)}")
        return {
            "jawline_score": 0,
            "cheekbones_score": 0,
            "symmetry_score": 0,
            "consistency": "0%",
            "recovery_checklist": []
        }


def analyze_facial(answers: list[dict], images: list[dict]) -> dict[str, Any] | None:
    try:
        logger.info(
            f"Starting facial analysis with {len(answers)} answers "
            f"and {len(images)} images"
        )

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
            "motivational_message": raw.get(
                "motivational_message",
                "Small daily facial exercises create noticeable long-term improvements. Keep going!"
            )
        }

        logger.info("Successfully completed facial analysis")
        return normalized

    except GeminiError as e:
        logger.error(f"Gemini AI error in facial analysis: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in facial analysis: {str(e)}", exc_info=True)
        return None

