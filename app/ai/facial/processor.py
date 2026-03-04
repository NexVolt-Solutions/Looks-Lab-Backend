from typing import Any, Optional

from app.ai.gemini_client import GeminiError, run_gemini_json
from app.ai.facial.prompts import build_context, prompt_facial_full
from app.core.logging import logger

_DEFAULT_FEATURES = [
    {"name": "Jawline",    "label": "Narrow",            "score": 75},
    {"name": "Nose",       "label": "Straight",           "score": 75},
    {"name": "Lips",       "label": "Medium",             "score": 75},
    {"name": "Cheek bones","label": "High",               "score": 75},
    {"name": "Eyes",       "label": "Almond",             "score": 75},
    {"name": "Ears",       "label": "Proportional",       "score": 75},
    {"name": "Face Shape", "label": "Diamond Face Shape", "score": 75},
]


def _safe(data: dict, key: str, default: Any = None) -> Any:
    return data.get(key, default) if data else default


def normalize_attributes(data: dict) -> dict[str, str]:
    try:
        attrs = _safe(data, "attributes", {})
        return {
            "symmetry":      attrs.get("symmetry", "Mostly"),
            "jawline":       attrs.get("jawline", "Medium/Slightly Defined"),
            "cheekbones":    attrs.get("cheekbones", "Medium/Normal"),
            "habits":        attrs.get("habits", "Medium/Normal"),
            "feature_goal":  attrs.get("feature_goal", "Overall improvement"),
            "exercise_time": attrs.get("exercise_time", "10-15 minutes"),
        }
    except Exception as e:
        logger.error(f"Error normalizing facial attributes: {e}")
        return {
            "symmetry": "Mostly", "jawline": "Medium/Slightly Defined",
            "cheekbones": "Medium/Normal", "habits": "Medium/Normal",
            "feature_goal": "Overall improvement", "exercise_time": "10-15 minutes",
        }


def normalize_feature_scores(data: dict) -> dict[str, Any]:
    try:
        scores = _safe(data, "feature_scores", {})
        features_raw = scores.get("features", [])

        features = [
            {"name": f.get("name", ""), "label": f.get("label", ""), "score": f.get("score", 0)}
            for f in (features_raw if isinstance(features_raw, list) else [])
            if isinstance(f, dict)
        ]

        return {
            "overall_score": scores.get("overall_score", 50),
            "features": features or _DEFAULT_FEATURES,
        }
    except Exception as e:
        logger.error(f"Error normalizing facial feature scores: {e}")
        return {"overall_score": 50, "features": []}


def normalize_daily_exercises(data: dict) -> dict[str, Any]:
    try:
        exercises_raw = _safe(data, "daily_exercises", [])
        if not isinstance(exercises_raw, list):
            return {"total": 0, "exercises": []}

        exercises = []
        for item in exercises_raw[:5]:
            if isinstance(item, dict):
                steps = item.get("steps", [])
                exercises.append({
                    "seq":      item.get("seq", len(exercises) + 1),
                    "title":    item.get("title", item.get("name", "Exercise")),
                    "duration": item.get("duration", "5 min"),
                    "steps":    [str(s) for s in steps if s] if isinstance(steps, list) else [],
                })

        return {"total": len(exercises), "exercises": exercises}
    except Exception as e:
        logger.error(f"Error normalizing facial exercises: {e}")
        return {"total": 0, "exercises": []}


def normalize_progress_tracking(data: dict) -> dict[str, Any]:
    try:
        progress  = _safe(data, "progress_tracking", {})
        checklist = progress.get("recovery_checklist", [])
        return {
            "jawline_score":    progress.get("jawline_score", 78),
            "cheekbones_score": progress.get("cheekbones_score", 72),
            "symmetry_score":   progress.get("symmetry_score", 75),
            "consistency":      progress.get("consistency", "0%"),
            "recovery_checklist": [str(i) for i in checklist[:3] if i] if isinstance(checklist, list) else [],
        }
    except Exception as e:
        logger.error(f"Error normalizing facial progress tracking: {e}")
        return {"jawline_score": 0, "cheekbones_score": 0, "symmetry_score": 0, "consistency": "0%", "recovery_checklist": []}


def analyze_facial(answers: list[dict], images: list[dict]) -> Optional[dict[str, Any]]:
    try:
        context = build_context(answers, images)
        raw = run_gemini_json(prompt_facial_full(context), domain="facial")

        if not raw:
            logger.warning("Empty response from Gemini for facial analysis")
            return None

        return {
            "attributes":           normalize_attributes(raw),
            "feature_scores":       normalize_feature_scores(raw),
            "daily_exercises":      normalize_daily_exercises(raw),
            "progress_tracking":    normalize_progress_tracking(raw),
            "motivational_message": raw.get("motivational_message", "Small daily facial exercises create noticeable long-term improvements. Keep going!"),
        }
    except GeminiError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in facial analysis: {e}", exc_info=True)
        return None

