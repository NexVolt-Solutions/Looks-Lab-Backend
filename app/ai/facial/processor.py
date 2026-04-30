from typing import Any, Optional

from app.ai.facial.prompts import build_context, prompt_facial_full
from app.ai.gemini_client import GeminiError, run_gemini_json
from app.core.logging import logger

_DEFAULT_FEATURES = [
    {"name": "Jawline", "label": "Narrow", "score": 75},
    {"name": "Nose", "label": "Straight", "score": 75},
    {"name": "Lips", "label": "Medium", "score": 75},
    {"name": "Cheek bones", "label": "High", "score": 75},
    {"name": "Eyes", "label": "Almond", "score": 75},
    {"name": "Ears", "label": "Proportional", "score": 75},
    {"name": "Face Shape", "label": "Diamond Face Shape", "score": 75},
]


def _safe(data: dict, key: str, default: Any = None) -> Any:
    return data.get(key, default) if data else default


def _normalize_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text or default


def _coerce_int(value: Any, default: int) -> int:
    try:
        numeric = int(float(value))
    except (TypeError, ValueError):
        return default
    return max(0, min(100, numeric))


def _default_attributes() -> dict[str, str]:
    return {
        "symmetry": "Mostly",
        "jawline": "Medium/Slightly Defined",
        "cheekbones": "Medium/Normal",
        "habits": "Moderate",
        "feature_goal": "Overall improvement",
        "exercise_time": "10-15 minutes",
    }


def _default_daily_exercises() -> dict[str, Any]:
    exercises = [
        {
            "seq": 1,
            "title": "Jawline Tightener",
            "duration": "5 min",
            "steps": [
                "Lift the chin slightly and keep the neck long.",
                "Move slowly and stay relaxed through the jaw.",
            ],
        },
        {
            "seq": 2,
            "title": "Lip Plumping",
            "duration": "2 min",
            "steps": [
                "Press and release the lips with gentle control.",
                "Keep the movement smooth and avoid straining.",
            ],
        },
        {
            "seq": 3,
            "title": "Cheek Lifts",
            "duration": "3 min",
            "steps": [
                "Lift the cheeks with a wide controlled smile.",
                "Hold briefly, then relax before repeating.",
            ],
        },
        {
            "seq": 4,
            "title": "Eye Firming",
            "duration": "4 min",
            "steps": [
                "Use light pressure only around the eye area.",
                "Keep the face relaxed while breathing steadily.",
            ],
        },
        {
            "seq": 5,
            "title": "Face Yoga Flow",
            "duration": "10 min",
            "steps": [
                "Move through each facial exercise with control.",
                "Stay consistent rather than forcing intensity.",
            ],
        },
    ]
    return {"total": len(exercises), "exercises": exercises}


def _default_progress_tracking() -> dict[str, Any]:
    return {
        "jawline_score": 78,
        "cheekbones_score": 72,
        "symmetry_score": 75,
        "consistency": "85%",
        "recovery_checklist": [
            "Did jawline exercises",
            "Did cheekbone exercises",
            "Did lips and eyes exercises",
        ],
    }


def normalize_attributes(data: dict) -> dict[str, str]:
    try:
        attrs = _safe(data, "attributes", {})
        defaults = _default_attributes()
        return {
            "symmetry": _normalize_text(attrs.get("symmetry"), defaults["symmetry"]),
            "jawline": _normalize_text(attrs.get("jawline"), defaults["jawline"]),
            "cheekbones": _normalize_text(attrs.get("cheekbones"), defaults["cheekbones"]),
            "habits": _normalize_text(attrs.get("habits"), defaults["habits"]),
            "feature_goal": _normalize_text(attrs.get("feature_goal"), defaults["feature_goal"]),
            "exercise_time": _normalize_text(attrs.get("exercise_time"), defaults["exercise_time"]),
        }
    except Exception as e:
        logger.error(f"Error normalizing facial attributes: {e}")
        return _default_attributes()


def normalize_feature_scores(data: dict) -> dict[str, Any]:
    try:
        scores = _safe(data, "feature_scores", {})
        features_raw = scores.get("features", [])

        features = [
            {
                "name": _normalize_text(feature.get("name")),
                "label": _normalize_text(feature.get("label")),
                "score": _coerce_int(feature.get("score"), 0),
            }
            for feature in (features_raw if isinstance(features_raw, list) else [])
            if isinstance(feature, dict)
        ]

        return {
            "overall_score": _coerce_int(scores.get("overall_score"), 50),
            "features": features or _DEFAULT_FEATURES,
        }
    except Exception as e:
        logger.error(f"Error normalizing facial feature scores: {e}")
        return {"overall_score": 50, "features": _DEFAULT_FEATURES}


def normalize_daily_exercises(data: dict) -> dict[str, Any]:
    try:
        exercises_raw = _safe(data, "daily_exercises", [])
        if not isinstance(exercises_raw, list):
            return _default_daily_exercises()

        exercises = []
        for item in exercises_raw[:5]:
            if isinstance(item, dict):
                steps = item.get("steps", [])
                exercises.append({
                    "seq": _coerce_int(item.get("seq"), len(exercises) + 1),
                    "title": _normalize_text(item.get("title", item.get("name")), "Exercise"),
                    "duration": _normalize_text(item.get("duration"), "5 min"),
                    "steps": [
                        _normalize_text(step) for step in steps
                        if _normalize_text(step)
                    ] if isinstance(steps, list) else [],
                })

        if not exercises:
            return _default_daily_exercises()
        return {"total": len(exercises), "exercises": exercises}
    except Exception as e:
        logger.error(f"Error normalizing facial exercises: {e}")
        return _default_daily_exercises()


def normalize_progress_tracking(data: dict) -> dict[str, Any]:
    try:
        progress = _safe(data, "progress_tracking", {})
        checklist = progress.get("recovery_checklist", [])
        normalized_checklist = [
            _normalize_text(item) for item in checklist[:3]
            if _normalize_text(item)
        ] if isinstance(checklist, list) else []
        defaults = _default_progress_tracking()
        return {
            "jawline_score": _coerce_int(progress.get("jawline_score"), defaults["jawline_score"]),
            "cheekbones_score": _coerce_int(progress.get("cheekbones_score"), defaults["cheekbones_score"]),
            "symmetry_score": _coerce_int(progress.get("symmetry_score"), defaults["symmetry_score"]),
            "consistency": _normalize_text(progress.get("consistency"), defaults["consistency"]),
            "recovery_checklist": normalized_checklist or defaults["recovery_checklist"],
        }
    except Exception as e:
        logger.error(f"Error normalizing facial progress tracking: {e}")
        return _default_progress_tracking()


def analyze_facial(answers: list[dict], images: list[dict]) -> Optional[dict[str, Any]]:
    try:
        context = build_context(answers, images)
        raw = run_gemini_json(prompt_facial_full(context), domain="facial")

        if not raw:
            logger.warning("Empty response from Gemini for facial analysis")
            return None

        return {
            "attributes": normalize_attributes(raw),
            "feature_scores": normalize_feature_scores(raw),
            "daily_exercises": normalize_daily_exercises(raw),
            "progress_tracking": normalize_progress_tracking(raw),
            "motivational_message": _normalize_text(
                raw.get("motivational_message"),
                "Small daily facial exercises create noticeable long-term improvements. Keep going!",
            ),
        }
    except GeminiError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in facial analysis: {e}", exc_info=True)
        return None
