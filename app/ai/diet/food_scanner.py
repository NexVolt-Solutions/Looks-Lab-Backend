from typing import Any, Optional

from app.ai.gemini_client import GeminiError, run_gemini_json
from app.core.logging import logger


def _build_food_prompt(image_url: str) -> str:
    return f"""
You are a professional nutritionist AI. Analyze the food in the image and return accurate nutrition information.

Image URL: {image_url}

Return STRICT JSON ONLY with this schema:
{{
  "food_name": "Grilled Chicken Salad",
  "portion_size": "1 bowl (350g)",
  "confidence": 92,
  "ingredients": [
    "Grilled chicken breast",
    "Romaine lettuce",
    "Cherry tomatoes",
    "Cucumber",
    "Olive oil dressing"
  ],
  "nutrition": {{
    "calories": 320,
    "protein": 35,
    "carbs": 12,
    "fat": 14,
    "fiber": 4,
    "sugar": 6
  }},
  "health_score": 85,
  "tip": "Great high-protein meal. Consider adding avocado for healthy fats."
}}

Rules:
- Estimate portion size visually from the image
- All nutrition values must be realistic for the identified food
- health_score is 0-100 (higher = healthier)
- confidence is 0-100 (how sure you are about the food identification)
- tip should be a short actionable diet advice specific to this food
- If image is not food, return food_name as "Not a food item" with all nutrition values as 0
"""


def _normalize_food_result(raw: dict) -> dict[str, Any]:
    try:
        nutrition_raw = raw.get("nutrition", {})
        if not isinstance(nutrition_raw, dict):
            nutrition_raw = {}

        nutrition = {k: round(float(nutrition_raw.get(k, 0)), 1)
                     for k in ["calories", "protein", "carbs", "fat", "fiber", "sugar"]}

        ingredients = raw.get("ingredients", [])
        health_score = max(0, min(100, int(raw.get("health_score", 0))))
        confidence   = max(0, min(100, int(raw.get("confidence", 0))))

        return {
            "food_name":    raw.get("food_name", "Unknown Food"),
            "portion_size": raw.get("portion_size", "1 serving"),
            "confidence":   confidence,
            "ingredients":  [str(i) for i in (ingredients if isinstance(ingredients, list) else [])[:10]],
            "nutrition":    nutrition,
            "health_score": health_score,
            "tip":          raw.get("tip", "Eat balanced meals for best results."),
        }
    except Exception as e:
        logger.error(f"Error normalizing food scan result: {e}")
        return {
            "food_name": "Unknown Food", "portion_size": "1 serving", "confidence": 0,
            "ingredients": [],
            "nutrition": {"calories": 0, "protein": 0, "carbs": 0, "fat": 0, "fiber": 0, "sugar": 0},
            "health_score": 0,
            "tip": "Could not analyze food. Please try with a clearer photo.",
        }


def analyze_food_image(image_url: str) -> Optional[dict[str, Any]]:
    if not image_url:
        logger.warning("analyze_food_image called with empty image_url")
        return None

    try:
        raw = run_gemini_json(_build_food_prompt(image_url), domain="diet_food_scan")

        if not raw:
            logger.warning("Empty response from Gemini for food scan")
            return None

        return _normalize_food_result(raw)

    except GeminiError as e:
        logger.error(f"Gemini AI error in food scan: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in food scan: {e}", exc_info=True)
        return None

