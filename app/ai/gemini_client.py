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
    if not text:
        return "{}"

    text = text.strip()

    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]

    if text.endswith("```"):
        text = text[:-3]

    text = text.strip()

    start_idx = text.find("{")
    end_idx = text.rfind("}")

    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        text = text[start_idx:end_idx + 1]

    return text


def _validate_json_structure(data: dict[str, Any], domain: str) -> None:
    if not isinstance(data, dict):
        raise GeminiValidationError(f"Expected dict, got {type(data).__name__}")

    if not data:
        raise GeminiValidationError("Empty response from AI")

    required_fields = {
        "skincare": ["attributes", "health", "concerns", "routine", "remedies", "products"],
        "haircare": ["attributes", "health", "concerns", "routine", "remedies", "products"],
        "facial": ["attributes", "feature_scores", "daily_exercises", "progress_tracking"],
        "fashion": ["attributes", "style_profile", "recommendations", "weekly_plan"],
        "workout": ["attributes", "routine", "progress_tracking"],
        "diet": ["attributes", "nutrition_summary", "daily_routine", "progress_tracking"],
        "height": ["attributes", "routine", "progress_tracking"],
        "quit porn": ["attributes", "recovery_path", "progress_tracking"],
    }

    domain_lower = domain.lower()
    if domain_lower in required_fields:
        missing_fields = [field for field in required_fields[domain_lower] if field not in data]
        if missing_fields:
            logger.warning(f"Missing fields in {domain} response: {missing_fields}")


def run_gemini_json(
        prompt: str,
        domain: str,
        model: str = None,
        timeout: int = 30,
        max_retries: int = 2
) -> dict[str, Any]:
    model_name = model or settings.GEMINI_MODEL

    for attempt in range(max_retries + 1):
        try:
            logger.info(f"Calling Gemini API for domain: {domain} (attempt {attempt + 1}/{max_retries + 1})")

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
                logger.error(f"JSON parsing failed after {max_retries + 1} attempts for {domain}")
                raise GeminiValidationError(f"Failed to parse JSON: {str(e)}")
            logger.warning(f"JSON parse error on attempt {attempt + 1}, retrying...")

        except TimeoutError:
            if attempt == max_retries:
                logger.error(f"Gemini API timeout after {max_retries + 1} attempts for {domain}")
                raise GeminiTimeoutError(f"API request timed out after {timeout}s")
            logger.warning(f"Timeout on attempt {attempt + 1}, retrying...")

        except Exception as e:
            error_msg = str(e).lower()

            if "rate limit" in error_msg or "quota" in error_msg:
                raise GeminiRateLimitError(f"Rate limit exceeded: {str(e)}")

            if attempt == max_retries:
                logger.error(f"Gemini API error after {max_retries + 1} attempts: {str(e)}", exc_info=True)
                raise GeminiError(f"AI processing failed: {str(e)}")

            logger.warning(f"Error on attempt {attempt + 1}: {str(e)}, retrying...")

    return {}


def run_gemini_json_safe(
        prompt: str,
        domain: str,
        fallback: dict[str, Any] | None = None
) -> dict[str, Any]:
    try:
        return run_gemini_json(prompt, domain)
    except GeminiError as e:
        logger.error(f"Gemini API error for {domain} (returning fallback): {str(e)}")
        return fallback or {}

