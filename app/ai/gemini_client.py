import json
from typing import Any, Optional

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


_REQUIRED_FIELDS: dict[str, list[str]] = {
    "skincare":   ["attributes", "health", "concerns", "routine", "remedies", "products"],
    "haircare":   ["attributes", "health", "concerns", "routine", "remedies", "products"],
    "facial":     ["attributes", "feature_scores", "daily_exercises", "progress_tracking"],
    "fashion":    ["attributes", "weekly_plan", "seasonal_style"],
    "workout":    ["attributes", "exercises", "progress_tracking"],
    "diet":       ["attributes", "nutrition_targets", "routine", "progress_tracking"],
    "height":     ["attributes", "today_focus", "daily_exercises", "progress_tracking"],
    "quit porn":  ["attributes", "recovery_path", "progress_tracking"],
}


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

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        text = text[start:end + 1]

    return text


def _validate_json_structure(data: dict[str, Any], domain: str) -> None:
    if not isinstance(data, dict):
        raise GeminiValidationError(f"Expected dict, got {type(data).__name__}")
    if not data:
        raise GeminiValidationError("Empty response from AI")

    required = _REQUIRED_FIELDS.get(domain.lower(), [])
    missing = [f for f in required if f not in data]
    if missing:
        logger.warning(f"Missing fields in {domain} response: {missing}. Continuing with available data.")


def run_gemini_json(
    prompt: str,
    domain: str,
    model: Optional[str] = None,
    timeout: int = 30,
    max_retries: int = 2,
) -> dict[str, Any]:
    model_name = model or settings.GEMINI_MODEL

    for attempt in range(max_retries + 1):
        try:
            logger.info(f"Gemini API call: domain={domain} attempt={attempt + 1}/{max_retries + 1}")

            response = genai.GenerativeModel(model_name).generate_content(
                prompt,
                request_options={"timeout": timeout}
            )

            if not response or not response.text:
                raise GeminiError("Empty response from Gemini API")

            cleaned = _clean_json_response(response.text)

            try:
                data = json.loads(cleaned)
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error for {domain}: {e}")
                raise GeminiValidationError(f"Invalid JSON in response: {e}")

            _validate_json_structure(data, domain)
            return data

        except GeminiValidationError:
            raise

        except TimeoutError:
            if attempt == max_retries:
                raise GeminiTimeoutError(f"Gemini API timed out after {timeout}s")
            logger.warning(f"Timeout on attempt {attempt + 1}, retrying...")

        except Exception as e:
            error_msg = str(e).lower()
            if "rate limit" in error_msg or "quota" in error_msg:
                raise GeminiRateLimitError(f"Rate limit exceeded: {e}")
            if attempt == max_retries:
                logger.error(f"Gemini API failed after {max_retries + 1} attempts: {e}", exc_info=True)
                raise GeminiError(f"AI processing failed: {e}")
            logger.warning(f"Error on attempt {attempt + 1}: {e}, retrying...")

    return {}


def run_gemini_json_safe(
    prompt: str,
    domain: str,
    fallback: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    try:
        return run_gemini_json(prompt, domain)
    except GeminiError as e:
        logger.error(f"Gemini API error for {domain} (returning fallback): {e}")
        return fallback or {}

