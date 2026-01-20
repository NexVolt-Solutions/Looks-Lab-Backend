import logging
import google.generativeai as genai
from app.core.config import settings

logger = logging.getLogger(__name__)

genai.configure(api_key=settings.GEMINI_API_KEY)

def run_gemini_json(prompt: str, model: str = settings.GEMINI_MODEL) -> dict:
    """
    Sends a prompt that requests strict JSON. Returns parsed dict or {}.
    """
    try:
        response = genai.GenerativeModel(model).generate_content(prompt)
        text = response.text or ""
        # Gemini often returns JSON in a code block; strip fences if present
        cleaned = text.strip().strip("```json").strip("```").strip()
        import json
        return json.loads(cleaned)
    except Exception as e:
        logger.error(f"Gemini JSON error: {e}")
        return {}

