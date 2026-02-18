"""
Fashion domain AI processor.
Analyzes user style preferences and generates personalized fashion recommendations.
"""
from typing import Any

from app.ai.gemini_client import run_gemini_json, GeminiError
from app.ai.fashion.prompts import prompt_fashion_full, build_context
from app.core.logging import logger


def _get_safe_value(data: dict, key: str, default: Any = None) -> Any:
    return data.get(key, default) if data else default


def normalize_attributes(data: dict) -> dict[str, Any]:
    """
    Matches Figma Your Style Profile screen:
    Body Type, Undertone, Style chips,
    Best Clothing Fits chips, Styles to Avoid chips,
    Warm Palette color swatches
    """
    try:
        attributes = _get_safe_value(data, "attributes", {})

        best_clothing_fits = attributes.get("best_clothing_fits", [])
        styles_to_avoid = attributes.get("styles_to_avoid", [])
        warm_palette = attributes.get("warm_palette", [])
        analyzing_insights = attributes.get("analyzing_insights", [])

        if not isinstance(best_clothing_fits, list):
            best_clothing_fits = []
        if not isinstance(styles_to_avoid, list):
            styles_to_avoid = []
        if not isinstance(warm_palette, list):
            warm_palette = []
        if not isinstance(analyzing_insights, list):
            analyzing_insights = []

        return {

            "body_type": attributes.get("body_type", "Athletic"),
            "undertone": attributes.get("undertone", "Warm"),
            "style": attributes.get("style", "Classic"),


            "best_clothing_fits": best_clothing_fits[:5],


            "styles_to_avoid": styles_to_avoid[:5],


            "warm_palette": warm_palette[:6],


            "analyzing_insights": analyzing_insights[:5],
        }
    except Exception as e:
        logger.error(f"Error normalizing fashion attributes: {str(e)}")
        return {
            "body_type": "Athletic",
            "undertone": "Warm",
            "style": "Classic",
            "best_clothing_fits": [],
            "styles_to_avoid": [],
            "warm_palette": [],
            "analyzing_insights": [],
        }


def normalize_weekly_plan(data: dict) -> list[dict[str, str]]:
    """
    Matches Figma Weekly Plan screen:
    Mon-Sun with daily style themes
    """
    try:
        weekly_plan = _get_safe_value(data, "weekly_plan", [])

        if not isinstance(weekly_plan, list):

            if isinstance(weekly_plan, dict):
                days_order = [
                    "Monday", "Tuesday", "Wednesday",
                    "Thursday", "Friday", "Saturday", "Sunday"
                ]
                weekly_plan = [
                    {"day": day, "theme": weekly_plan.get(day, "Casual")}
                    for day in days_order
                ]
            else:
                weekly_plan = []

        cleaned = []
        for item in weekly_plan[:7]:
            if isinstance(item, dict):
                cleaned.append({
                    "day": item.get("day", ""),
                    "theme": item.get("theme", "Casual")
                })

        return cleaned
    except Exception as e:
        logger.error(f"Error normalizing fashion weekly plan: {str(e)}")
        return []


def normalize_seasonal_style(data: dict) -> dict[str, dict[str, list]]:
    """
    Matches Figma Weekly Plan - Seasonal Style section:
    Summer / Monsoon / Winter tabs
    Each with outfit_combinations, recommended_fabrics, footwear chips
    """
    try:
        seasonal = _get_safe_value(data, "seasonal_style", {})

        result = {}
        for season in ["summer", "monsoon", "winter"]:
            season_data = seasonal.get(season, {})

            outfit_combinations = season_data.get("outfit_combinations", [])
            recommended_fabrics = season_data.get("recommended_fabrics", [])
            footwear = season_data.get("footwear", [])

            if not isinstance(outfit_combinations, list):
                outfit_combinations = []
            if not isinstance(recommended_fabrics, list):
                recommended_fabrics = []
            if not isinstance(footwear, list):
                footwear = []

            result[season] = {
                "outfit_combinations": outfit_combinations[:5],
                "recommended_fabrics": recommended_fabrics[:5],
                "footwear": footwear[:5]
            }

        return result
    except Exception as e:
        logger.error(f"Error normalizing fashion seasonal style: {str(e)}")
        return {
            "summer": {"outfit_combinations": [], "recommended_fabrics": [], "footwear": []},
            "monsoon": {"outfit_combinations": [], "recommended_fabrics": [], "footwear": []},
            "winter": {"outfit_combinations": [], "recommended_fabrics": [], "footwear": []}
        }


def analyze_fashion(answers: list[dict], images: list[dict]) -> dict[str, Any] | None:
    try:
        logger.info(
            f"Starting fashion analysis with {len(answers)} answers "
            f"and {len(images)} images"
        )

        context = build_context(answers, images)
        prompt = prompt_fashion_full(context)

        raw = run_gemini_json(prompt, domain="fashion")

        if not raw:
            logger.warning("Empty response from Gemini for fashion analysis")
            return None

        normalized = {
            "attributes": normalize_attributes(raw),
            "routine": {
                "weekly_plan": normalize_weekly_plan(raw),
                "seasonal_style": normalize_seasonal_style(raw),
            },
            "motivational_message": raw.get(
                "motivational_message",
                "Your style is your identity. Own it with confidence every day!"
            )
        }

        logger.info("Successfully completed fashion analysis")
        return normalized

    except GeminiError as e:
        logger.error(f"Gemini AI error in fashion analysis: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in fashion analysis: {str(e)}", exc_info=True)
        return None

