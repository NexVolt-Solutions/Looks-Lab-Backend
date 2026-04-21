import json
import re
from typing import Any, Optional

import google.generativeai as genai

from app.core.config import settings
from app.core.logging import logger

# configure once
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
    """Trim code fences, remove common non-JSON tokens (end markers, heredocs), extract outer-most JSON, and normalize a few common non-JSON examples.

    This function is intentionally conservative: it only mutates obvious non-JSON tokens that appear in
    the prompt examples (for example `0-100` ranges). It avoids aggressive transformations that could
    corrupt real content.
    """
    if not text:
        return "{}"

    # Normalize whitespace and strip common markdown fences
    text = text.strip()

    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]

    if text.endswith("```"):
        text = text[:-3]

    text = text.strip()

    # Remove common model-control tokens like <|endoftext|> or literal end markers
    text = re.sub(r'^(?:\ufeff\s*)?(?:<\|endoftext\|>|END_OF_TEXT|endoftext)\s*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'(?:<\|endoftext\|>|END_OF_TEXT|endoftext)\s*$', '', text, flags=re.IGNORECASE)

    # Remove heredoc markers and their matching terminators (<<EOF ... EOF)
    text = re.sub(r'<<-?EOF\s*\n', '', text)
    text = re.sub(r'\nEOF\s*$', '', text, flags=re.IGNORECASE)

    # Remove simple "Response:", "JSON:", or "Output:" prefixes that some prompts include
    text = re.sub(r'^\s*(Response|JSON|Output)\s*[:\-]\s*', '', text, flags=re.IGNORECASE)

    # Extract the outer-most JSON object if present
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        text = text[start : end + 1]

    # Normalize simple numeric ranges like "0-100" to a single integer placeholder (0)
    # Only replace when it appears as a bare number range (e.g. : 0-100 or "confidence": 0-100)
    # Avoid variable-width lookbehind (unsupported); capture the prefix and reinsert it.
    text = re.sub(r'(:\s*)\d+\s*-\s*\d+', r'\1 0', text)

    # Strip surrounding quotes that some models include around the whole JSON
    if text.startswith('"') and text.endswith('"'):
        # remove a single pair of wrapping quotes and unescape simple escaped quotes inside
        inner = text[1:-1]
        inner = inner.replace('\\"', '"')
        text = inner

    # Sometimes models include unquoted True/False/null with different casing; keep as-is but
    # developers should prefer the model to return strictly valid JSON. We do not try to fix all cases.

    return text


def _extract_text_from_response(response: Any) -> str:
    """Robustly extract text content from different shapes of SDK responses.

    The google.generativeai SDK may return objects with different attribute names depending on
    SDK version or model. Try several common access patterns.
    """
    if not response:
        return ""

    # If the SDK gives a plain string
    if isinstance(response, str):
        return response

    # Common attribute on a simple wrapper
    for attr in ("text", "content", "output", "message", "response", "result"):
        if hasattr(response, attr):
            val = getattr(response, attr)
            if isinstance(val, str) and val.strip():
                return val

    # Some SDKs return an object with candidates or outputs list
    try:
        if hasattr(response, "candidates") and response.candidates:
            first = response.candidates[0]
            # candidate may have different field names
            for a in ("content", "text", "message"):
                if hasattr(first, a):
                    val = getattr(first, a)
                    if isinstance(val, str) and val.strip():
                        return val
    except Exception:
        pass

    try:
        # Try dict-like access
        if isinstance(response, dict):
            for key in ("text", "content", "output", "candidates"):
                if key in response and response[key]:
                    val = response[key]
                    if isinstance(val, list) and val:
                        # take first candidate
                        first = val[0]
                        if isinstance(first, dict):
                            for a in ("content", "text"):
                                if a in first and isinstance(first[a], str):
                                    return first[a]
                        if isinstance(first, str):
                            return first
                    if isinstance(val, str):
                        return val
    except Exception:
        pass

    # Fallback to stringifying the response
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
    missing = [f for f in required if f not in data]
    if missing:
        # Log missing fields but do not raise — some domains are allowed to be partial.
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

            # Try with JSON mode first to force valid JSON output
            try:
                response = genai.GenerativeModel(model_name).generate_content(
                    prompt,
                    generation_config=genai.GenerationConfig(
                        temperature=0.5,
                        max_output_tokens=8192,
                        response_mime_type="application/json",
                    ),
                    request_options={"timeout": timeout},
                )
            except Exception:
                # Fallback if model does not support JSON mode
                response = genai.GenerativeModel(model_name).generate_content(
                    prompt,
                    generation_config=genai.GenerationConfig(
                        temperature=0.5,
                        max_output_tokens=8192,
                    ),
                    request_options={"timeout": timeout},
                )

            text = _extract_text_from_response(response)
            if not text or not text.strip():
                raise GeminiError("Empty response from Gemini API")

            cleaned = _clean_json_response(text)

            try:
                data = json.loads(cleaned)
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error for {domain}: {e}; cleaned_text={cleaned[:200]}")
                raise GeminiValidationError(f"Invalid JSON in response: {e}")

            _validate_json_structure(data, domain)
            return data

        except GeminiValidationError:
            # If we receive invalid JSON, do not retry — caller should handle this
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

        