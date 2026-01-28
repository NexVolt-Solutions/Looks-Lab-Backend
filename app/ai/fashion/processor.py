"""
Fashion domain AI processor.
Analyzes user style preferences and generates personalized fashion recommendations.
"""
from typing import Any

from app.ai.gemini_client import run_gemini_json, GeminiError
from app.ai.fashion.prompts import prompt_fashion_full
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


def normalize_attributes(data: dict) -> dict[str, Any]:
    try:
        attributes = _get_safe_value(data, "attributes", {})

        return {
            "body_type": attributes.get("body_type", "Average"),
            "body_type_confidence": attributes.get("body_type_confidence", 0),
            "undertone": attributes.get("undertone", "Neutral"),
            "undertone_confidence": attributes.get("undertone_confidence", 0),
            "style_goal": attributes.get("style_goal", "Confidence"),
            "style_goal_confidence": attributes.get("style_goal_confidence", 0),
        }
    except Exception as e:
        logger.error(f"Error normalizing fashion attributes: {str(e)}")
        return {
            "body_type": "Average",
            "body_type_confidence": 0,
            "undertone": "Neutral",
            "undertone_confidence": 0,
            "style_goal": "Confidence",
            "style_goal_confidence": 0,
        }


def normalize_style_profile(data: dict) -> dict[str, Any]:
    try:
        profile = _get_safe_value(data, "style_profile", {})

        return {
            "style": profile.get("style", "Classic"),
            "style_confidence": profile.get("style_confidence", 0),
            "fit_preference": profile.get("fit_preference", "Regular"),
            "fit_confidence": profile.get("fit_confidence", 0),
            "trend_preference": profile.get("trend_preference", "Sometimes"),
            "trend_confidence": profile.get("trend_confidence", 0),
            "accessories": profile.get("accessories", "Occasionally"),
            "accessories_confidence": profile.get("accessories_confidence", 0),
        }
    except Exception as e:
        logger.error(f"Error normalizing fashion style profile: {str(e)}")
        return {
            "style": "Classic",
            "style_confidence": 0,
            "fit_preference": "Regular",
            "fit_confidence": 0,
            "trend_preference": "Sometimes",
            "trend_confidence": 0,
            "accessories": "Occasionally",
            "accessories_confidence": 0,
        }


def normalize_recommendations(data: dict) -> dict[str, list]:
    try:
        recommendations = _get_safe_value(data, "recommendations", {})

        best_fits = recommendations.get("best_fits", [])
        avoid_styles = recommendations.get("avoid_styles", [])
        color_palette = recommendations.get("color_palette", [])

        if not isinstance(best_fits, list):
            best_fits = []
        if not isinstance(avoid_styles, list):
            avoid_styles = []
        if not isinstance(color_palette, list):
            color_palette = []

        return {
            "best_fits": best_fits[:5],
            "avoid_styles": avoid_styles[:5],
            "color_palette": color_palette[:6]
        }
    except Exception as e:
        logger.error(f"Error normalizing fashion recommendations: {str(e)}")
        return {
            "best_fits": [],
            "avoid_styles": [],
            "color_palette": []
        }


def normalize_weekly_plan(data: dict) -> dict[str, str]:
    try:
        plan = _get_safe_value(data, "weekly_plan", {})

        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        return {day: plan.get(day, "Casual") for day in days}
    except Exception as e:
        logger.error(f"Error normalizing fashion weekly plan: {str(e)}")
        return {
            "Monday": "Casual",
            "Tuesday": "Casual",
            "Wednesday": "Casual",
            "Thursday": "Casual",
            "Friday": "Casual",
            "Saturday": "Casual",
            "Sunday": "Casual",
        }


def normalize_seasonal_style(data: dict) -> dict[str, dict[str, list]]:
    try:
        seasonal = _get_safe_value(data, "seasonal_style", {})

        result = {}
        for season in ["Summer", "Monsoon", "Winter"]:
            season_data = seasonal.get(season, {})

            outfits = season_data.get("outfits", [])
            fabrics = season_data.get("fabrics", [])
            footwear = season_data.get("footwear", [])

            if not isinstance(outfits, list):
                outfits = []
            if not isinstance(fabrics, list):
                fabrics = []
            if not isinstance(footwear, list):
                footwear = []

            result[season] = {
                "outfits": outfits[:5],
                "fabrics": fabrics[:5],
                "footwear": footwear[:5]
            }

        return result
    except Exception as e:
        logger.error(f"Error normalizing fashion seasonal style: {str(e)}")
        return {
            "Summer": {"outfits": [], "fabrics": [], "footwear": []},
            "Monsoon": {"outfits": [], "fabrics": [], "footwear": []},
            "Winter": {"outfits": [], "fabrics": [], "footwear": []}
        }


def analyze_fashion(answers: list[dict], images: list[dict]) -> dict[str, Any] | None:
    try:
        logger.info(f"Starting fashion analysis with {len(answers)} answers and {len(images)} images")

        context = build_context(answers, images)
        prompt = prompt_fashion_full(context)

        raw = run_gemini_json(prompt, domain="fashion")

        if not raw:
            logger.warning("Empty response from Gemini for fashion analysis")
            return None

        normalized = {
            "attributes": normalize_attributes(raw),
            "style_profile": normalize_style_profile(raw),
            "recommendations": normalize_recommendations(raw),
            "weekly_plan": normalize_weekly_plan(raw),
            "seasonal_style": normalize_seasonal_style(raw),
        }

        logger.info("Successfully completed fashion analysis")
        return normalized

    except GeminiError as e:
        logger.error(f"Gemini AI error in fashion analysis: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in fashion analysis: {str(e)}", exc_info=True)
        return None

