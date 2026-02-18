"""
Gemini AI client.
Handles communication with Google's Gemini API for AI analysis.
"""
import json
from typing import Any

import google.generativeai as genai

from app.core.config import settings
from app.core.logging import logger

genai.configure(api_key=settings.GEMINI_API_KEY)


class GeminiError(Exception):
    pass


class GeminiTimeoutError(GeminiError):
    pass


class GeminiValidationError(GeminiError):
    pass


class GeminiRateLimitError(GeminiError):
    pass


def _clean_json_response(text: str) -> str:
    """
    Clean raw Gemini response text to extract valid JSON.
    Handles markdown code blocks and extra whitespace.
    """
    if not text:
        return "{}"

    text = text.strip()

    # Strip markdown code fences
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]

    if text.endswith("```"):
        text = text[:-3]

    text = text.strip()

    # Extract JSON object boundaries
    start_idx = text.find("{")
    end_idx = text.rfind("}")

    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        text = text[start_idx:end_idx + 1]

    return text


def _validate_json_structure(data: dict[str, Any], domain: str) -> None:
    """
    Validate that AI response contains expected top-level fields.
    Logs warnings for missing fields but does NOT raise exceptions
    so partial responses can still be used.
    """
    if not isinstance(data, dict):
        raise GeminiValidationError(f"Expected dict, got {type(data).__name__}")

    if not data:
        raise GeminiValidationError("Empty response from AI")

    # ✅ Updated to match all processor output keys after our fixes
    required_fields = {

        # Skincare: 6 attributes, 5 health, 5 concerns
        "skincare": [
            "attributes",       # skin_type, sensitivity, elasticity, oil_balance, hydration, pore_visibility
            "health",           # skin_health, texture, skin_barrier, smoothness, brightness
            "concerns",         # acne_breakouts, pigmentation, darkness_spot, wrinkles, uneven_tone
            "routine",          # today[], night[]
            "remedies",         # remedies[], safety_tips[]
            "products",         # name, tags[], time_of_day, overview, how_to_use[], etc.
        ],

        # Haircare: same structure as skincare
        "haircare": [
            "attributes",       # density, hair_type, volume, texture
            "health",           # scalp_health, breakage, frizz_dryness, dandruff
            "concerns",         # hairloss, hairline_recession, stage
            "routine",          # today[], night[]
            "remedies",         # remedies[], safety_tips[]
            "products",         # name, tags[], time_of_day, overview, etc.
        ],

        # Facial: feature scores + structured exercises
        "facial": [
            "attributes",       # symmetry, jawline, cheekbones, habits, feature_goal, exercise_time
            "feature_scores",   # overall_score, features:[{name, label, score}]
            "daily_exercises",  # [{seq, title, duration, steps[]}]
            "progress_tracking", # jawline_score, cheekbones_score, symmetry_score, consistency, recovery_checklist
        ],

        # Fashion: merged attributes + weekly plan + seasonal
        "fashion": [
            "attributes",       # body_type, undertone, style, best_clothing_fits[], styles_to_avoid[], warm_palette[]
            "weekly_plan",      # [{day, theme}] x 7
            "seasonal_style",   # summer/monsoon/winter: {outfit_combinations[], recommended_fabrics[], footwear[]}
        ],

        # Workout: intensity/activity + structured exercises
        "workout": [
            "attributes",       # intensity, activity, goal, diet_type, today_focus[], posture_insight, workout_summary
            "exercises",        # morning/evening: [{seq, title, duration, steps[]}]
            "progress_tracking", # weekly_calories, consistency, strength_gain, fitness_consistency, recovery_checklist
        ],

        # Diet: calories + structured meals + nutrition targets
        "diet": [
            "attributes",       # calories_intake, activity, goal, diet_type, today_focus[], posture_insight, meals_summary
            "nutrition_targets", # daily_calories, protein_g, carbs_g, fat_g, water_glasses, fiber_g
            "routine",          # morning/evening: [{seq, title, description, time}]
            "progress_tracking", # daily_calories, consistency, nutrition_balance, diet_consistency, calorie_balance, recovery_checklist
        ],

        # Height: posture + structured exercises + today focus
        "height": [
            "attributes",       # current_height, goal_height, growth_potential, posture_status, bmi_status
            "today_focus",      # [{title, duration}]
            "daily_exercises",  # morning/evening: [{seq, title, duration, steps[]}]
            "progress_tracking", # completion_percent, posture_gain_cm, consistency
        ],

        # Quit Porn: streak + daily tasks + exercises
        "quit porn": [
            "attributes",       # frequency, triggers[], urge_timing[], coping_mechanisms, commitment_level
            "recovery_path",    # streak:{current,longest,next_goal,message}, daily_tasks[], exercises[]
            "progress_tracking", # consistency, recovery_score, recovery_checklist[]
        ],
    }

    domain_lower = domain.lower()
    if domain_lower in required_fields:
        missing_fields = [
            field for field in required_fields[domain_lower]
            if field not in data
        ]
        if missing_fields:
            logger.warning(
                f"Missing fields in {domain} response: {missing_fields}. "
                f"Processing will continue with available data."
            )


def run_gemini_json(
        prompt: str,
        domain: str,
        model: str = None,
        timeout: int = 30,
        max_retries: int = 2
) -> dict[str, Any]:
    """
    Call Gemini API and return parsed JSON response.

    Args:
        prompt: Full prompt string
        domain: Domain name for logging and validation
        model: Override model name (uses settings.GEMINI_MODEL by default)
        timeout: Request timeout in seconds
        max_retries: Number of retry attempts on failure

    Returns:
        Parsed JSON dict from Gemini response

    Raises:
        GeminiTimeoutError: If all attempts timeout
        GeminiRateLimitError: If rate limited
        GeminiValidationError: If JSON parsing fails
        GeminiError: For other Gemini errors
    """
    model_name = model or settings.GEMINI_MODEL

    for attempt in range(max_retries + 1):
        try:
            logger.info(
                f"Calling Gemini API for domain: {domain} "
                f"(attempt {attempt + 1}/{max_retries + 1})"
            )

            response = genai.GenerativeModel(model_name).generate_content(
                prompt,
                request_options={"timeout": timeout}
            )

            if not response or not response.text:
                raise GeminiError("Empty response from Gemini API")

            text = response.text
            logger.debug(f"Raw Gemini response length: {len(text)} chars")

            cleaned_text = _clean_json_response(text)

            try:
                parsed_data = json.loads(cleaned_text)
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error for {domain}: {str(e)}")
                logger.debug(f"Failed JSON text: {cleaned_text[:500]}...")
                raise GeminiValidationError(f"Invalid JSON in response: {str(e)}")

            _validate_json_structure(parsed_data, domain)

            logger.info(f"Successfully parsed Gemini response for {domain}")
            return parsed_data

        except json.JSONDecodeError as e:
            if attempt == max_retries:
                logger.error(
                    f"JSON parsing failed after {max_retries + 1} attempts "
                    f"for {domain}"
                )
                raise GeminiValidationError(f"Failed to parse JSON: {str(e)}")
            logger.warning(f"JSON parse error on attempt {attempt + 1}, retrying...")

        except TimeoutError:
            if attempt == max_retries:
                logger.error(
                    f"Gemini API timeout after {max_retries + 1} attempts "
                    f"for {domain}"
                )
                raise GeminiTimeoutError(f"API request timed out after {timeout}s")
            logger.warning(f"Timeout on attempt {attempt + 1}, retrying...")

        except GeminiValidationError:
            # Don't retry validation errors — re-raise immediately
            raise

        except Exception as e:
            error_msg = str(e).lower()

            if "rate limit" in error_msg or "quota" in error_msg:
                raise GeminiRateLimitError(f"Rate limit exceeded: {str(e)}")

            if attempt == max_retries:
                logger.error(
                    f"Gemini API error after {max_retries + 1} attempts: {str(e)}",
                    exc_info=True
                )
                raise GeminiError(f"AI processing failed: {str(e)}")

            logger.warning(f"Error on attempt {attempt + 1}: {str(e)}, retrying...")

    return {}


def run_gemini_json_safe(
        prompt: str,
        domain: str,
        fallback: dict[str, Any] | None = None
) -> dict[str, Any]:
    """
    Safe wrapper around run_gemini_json.
    Returns fallback dict instead of raising on error.

    Args:
        prompt: Full prompt string
        domain: Domain name for logging and validation
        fallback: Dict to return on failure (default: empty dict)

    Returns:
        Parsed JSON dict or fallback
    """
    try:
        return run_gemini_json(prompt, domain)
    except GeminiError as e:
        logger.error(
            f"Gemini API error for {domain} (returning fallback): {str(e)}"
        )
        return fallback or {}

