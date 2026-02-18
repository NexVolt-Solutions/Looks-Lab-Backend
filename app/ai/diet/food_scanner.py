"""
Food image analysis using Gemini AI vision.
Used by the diet domain for food scanning feature.
"""
from typing import Any

from app.ai.gemini_client import run_gemini_json, GeminiError
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
    """
    Normalize and validate Gemini response.
    Ensures all required fields are present with correct types.
    """
    try:
        # ── Nutrition ─────────────────────────────────────────
        nutrition_raw = raw.get("nutrition", {})
        if not isinstance(nutrition_raw, dict):
            nutrition_raw = {}

        nutrition = {
            "calories": round(float(nutrition_raw.get("calories", 0)), 1),
            "protein":  round(float(nutrition_raw.get("protein", 0)), 1),
            "carbs":    round(float(nutrition_raw.get("carbs", 0)), 1),
            "fat":      round(float(nutrition_raw.get("fat", 0)), 1),
            "fiber":    round(float(nutrition_raw.get("fiber", 0)), 1),
            "sugar":    round(float(nutrition_raw.get("sugar", 0)), 1),
        }

        # ── Ingredients ───────────────────────────────────────
        ingredients = raw.get("ingredients", [])
        if not isinstance(ingredients, list):
            ingredients = []

        # ── Scores ────────────────────────────────────────────
        health_score = raw.get("health_score", 0)
        confidence = raw.get("confidence", 0)

        # Clamp both to 0-100
        health_score = max(0, min(100, int(health_score)))
        confidence = max(0, min(100, int(confidence)))

        return {
            "food_name":    raw.get("food_name", "Unknown Food"),
            "portion_size": raw.get("portion_size", "1 serving"),
            "confidence":   confidence,
            "ingredients":  [str(i) for i in ingredients[:10]],
            "nutrition":    nutrition,
            "health_score": health_score,
            "tip":          raw.get("tip", "Eat balanced meals for best results."),
        }

    except Exception as e:
        logger.error(f"Error normalizing food scan result: {e}")
        return {
            "food_name":    "Unknown Food",
            "portion_size": "1 serving",
            "confidence":   0,
            "ingredients":  [],
            "nutrition": {
                "calories": 0,
                "protein":  0,
                "carbs":    0,
                "fat":      0,
                "fiber":    0,
                "sugar":    0,
            },
            "health_score": 0,
            "tip": "Could not analyze food. Please try with a clearer photo.",
        }


def analyze_food_image(image_url: str) -> dict[str, Any] | None:
    """
    Analyze a food image using Gemini AI vision.

    Args:
        image_url: URL or S3 path of the food image

    Returns:
        Normalized nutrition dict or None if analysis fails

    Used by:
        POST /domains/diet/foods/analyze
    """
    if not image_url:
        logger.warning("analyze_food_image called with empty image_url")
        return None

    try:
        logger.info(f"Analyzing food image: {image_url}")

        prompt = _build_food_prompt(image_url)
        raw = run_gemini_json(prompt, domain="diet_food_scan")

        if not raw:
            logger.warning("Empty response from Gemini for food scan")
            return None

        result = _normalize_food_result(raw)

        logger.info(
            f"Food scan complete: {result['food_name']} | "
            f"{result['nutrition']['calories']} kcal | "
            f"confidence: {result['confidence']}%"
        )

        return result

    except GeminiError as e:
        logger.error(f"Gemini AI error in food scan: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in food scan: {e}", exc_info=True)
        return None

