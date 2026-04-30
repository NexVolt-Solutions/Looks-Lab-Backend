import json
import re
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from typing import Any, Optional

from google import genai
from google.genai import types

from app.core.config import settings
from app.core.logging import logger

_CLIENT = genai.Client(api_key=settings.GEMINI_API_KEY)


class GeminiError(Exception):
    pass


class GeminiTimeoutError(GeminiError):
    pass


class GeminiValidationError(GeminiError):
    pass


class GeminiRateLimitError(GeminiError):
    pass


_REQUIRED_FIELDS: dict[str, list[str]] = {
    "skincare": ["attributes", "health", "concerns", "routine", "remedies", "products"],
    "haircare": ["attributes", "health", "concerns", "routine", "remedies", "products"],
    "facial": ["attributes", "feature_scores", "daily_exercises", "progress_tracking"],
    "fashion": ["attributes", "weekly_plan", "seasonal_style"],
    "workout": ["attributes", "exercises", "progress_tracking"],
    "diet": ["attributes", "nutrition_targets", "routine", "progress_tracking"],
    "height": ["attributes", "today_focus", "daily_exercises", "progress_tracking"],
    "quit porn": ["attributes", "recovery_path", "progress_tracking"],
}


def _clean_json_response(text: str) -> str:
    """Trim obvious wrappers and extract the outer-most JSON object."""
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
    text = re.sub(r'^(?:\ufeff\s*)?(?:<\|endoftext\|>|END_OF_TEXT|endoftext)\s*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'(?:<\|endoftext\|>|END_OF_TEXT|endoftext)\s*$', '', text, flags=re.IGNORECASE)
    text = re.sub(r'<<-?EOF\s*\n', '', text)
    text = re.sub(r'\nEOF\s*$', '', text, flags=re.IGNORECASE)
    text = re.sub(r'^\s*(Response|JSON|Output)\s*[:\-]\s*', '', text, flags=re.IGNORECASE)

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        text = text[start : end + 1]

    text = re.sub(r'(:\s*)\d+\s*-\s*\d+', r'\1 0', text)

    if text.startswith('"') and text.endswith('"'):
        inner = text[1:-1]
        inner = inner.replace('\\"', '"')
        text = inner

    return text


def _extract_text_from_response(response: Any) -> str:
    """Robustly extract text content from different response shapes."""
    if not response:
        return ""

    if isinstance(response, str):
        return response

    for attr in ("text", "content", "output", "message", "response", "result"):
        if hasattr(response, attr):
            val = getattr(response, attr)
            if isinstance(val, str) and val.strip():
                return val

    try:
        if hasattr(response, "candidates") and response.candidates:
            first = response.candidates[0]
            for attr in ("content", "text", "message"):
                if hasattr(first, attr):
                    val = getattr(first, attr)
                    if isinstance(val, str) and val.strip():
                        return val
    except Exception:
        pass

    try:
        if isinstance(response, dict):
            for key in ("text", "content", "output", "candidates"):
                if key in response and response[key]:
                    val = response[key]
                    if isinstance(val, list) and val:
                        first = val[0]
                        if isinstance(first, dict):
                            for attr in ("content", "text"):
                                if attr in first and isinstance(first[attr], str):
                                    return first[attr]
                        if isinstance(first, str):
                            return first
                    if isinstance(val, str):
                        return val
    except Exception:
        pass

    try:
        return str(response)
    except Exception:
        return ""


def _validate_json_structure(data: dict[str, Any], domain: str) -> None:
    if not isinstance(data, dict):
        raise GeminiValidationError(f"Expected dict, got {type(data).__name__}")
    if not data:
        raise GeminiValidationError("Empty response from AI")

    required = _REQUIRED_FIELDS.get(domain.lower(), [])
    missing = [field for field in required if field not in data]
    if missing:
        logger.warning(f"Missing fields in {domain} response: {missing}. Continuing with available data.")


def _generate_content(
    model_name: str,
    contents: Any,
    config: types.GenerateContentConfig,
    timeout: int,
) -> Any:
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(
            lambda: _CLIENT.models.generate_content(
                model=model_name,
                contents=contents,
                config=config,
            )
        )
        try:
            return future.result(timeout=timeout)
        except FuturesTimeoutError as exc:
            future.cancel()
            raise GeminiTimeoutError(f"Gemini API timed out after {timeout}s") from exc


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

            try:
                response = _generate_content(
                    model_name=model_name,
                    contents=prompt,
                    timeout=timeout,
                    config=types.GenerateContentConfig(
                        temperature=0.5,
                        max_output_tokens=8192,
                        response_mime_type="application/json",
                    ),
                )
            except GeminiTimeoutError:
                raise
            except Exception:
                response = _generate_content(
                    model_name=model_name,
                    contents=prompt,
                    timeout=timeout,
                    config=types.GenerateContentConfig(
                        temperature=0.5,
                        max_output_tokens=8192,
                    ),
                )

            text = _extract_text_from_response(response)
            if not text or not text.strip():
                raise GeminiError("Empty response from Gemini API")

            cleaned = _clean_json_response(text)

            try:
                data = json.loads(cleaned)
            except json.JSONDecodeError as exc:
                logger.error(f"JSON decode error for {domain}: {exc}; cleaned_text={cleaned[:200]}")
                raise GeminiValidationError(f"Invalid JSON in response: {exc}")

            _validate_json_structure(data, domain)
            return data

        except GeminiValidationError:
            raise
        except GeminiTimeoutError:
            if attempt == max_retries:
                raise
            logger.warning(f"Timeout on attempt {attempt + 1}, retrying...")
        except Exception as exc:
            error_msg = str(exc).lower()
            if "rate limit" in error_msg or "quota" in error_msg or "429" in error_msg:
                raise GeminiRateLimitError(f"Rate limit exceeded: {exc}")
            if attempt == max_retries:
                logger.error(f"Gemini API failed after {max_retries + 1} attempts: {exc}", exc_info=True)
                raise GeminiError(f"AI processing failed: {exc}")
            logger.warning(f"Error on attempt {attempt + 1}: {exc}, retrying...")

    return {}


def run_gemini_json_safe(
    prompt: str,
    domain: str,
    fallback: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    try:
        return run_gemini_json(prompt, domain)
    except GeminiError as exc:
        logger.error(f"Gemini API error for {domain} (returning fallback): {exc}")
        return fallback or {}
