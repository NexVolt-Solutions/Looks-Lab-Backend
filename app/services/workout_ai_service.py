import json
import re
from datetime import datetime, timezone

import google.generativeai as genai

from app.core.config import settings
from app.core.logging import logger
from app.schemas.workout import WorkoutFocus

genai.configure(api_key=settings.GEMINI_API_KEY)


def _clean_json_response(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"\s*```$", "", text, flags=re.MULTILINE)
    text = text.strip()
    start = text.find("{")
    if start == -1:
        return text
    depth = 0
    for i, ch in enumerate(text[start:], start):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
    return text[start:]


def _sanitize_json_text(text: str) -> str:
    text = text.replace('\u2018', "'").replace('\u2019', "'")
    text = text.replace('\u201c', '"').replace('\u201d', '"')
    text = re.sub(r',\s*([}\]])', r'\1', text)
    return text


class WorkoutAIService:

    @staticmethod
    def generate_workout_plan(
        focus: WorkoutFocus,
        user_data: dict,
        intensity: str = "moderate",
        duration_minutes: int = 30,
    ) -> dict:
        focus_label = focus.value.replace('_', ' ').title()
        age = user_data.get('age', 25)
        gender = user_data.get('gender', 'male')
        level = user_data.get('fitness_level', 'beginner')
        equipment = user_data.get('equipment', 'none')

        prompt = (
            f'Return ONLY valid JSON. No markdown. No apostrophes in strings.\n\n'
            f'Create a {focus_label} workout plan for: age {age}, {gender}, level {level}, '
            f'equipment {equipment}, intensity {intensity}, duration {duration_minutes} min.\n\n'
            f'Use exactly this structure:\n'
            '{{"focus":"' + focus.value + '",'
            '"title":"Short catchy title",'
            '"description":"One motivational sentence",'
            f'"duration_minutes":{duration_minutes},'
            '"exercise_count":6,'
            f'"intensity":"{intensity}",'
            '"insight":{"title":"Short tip title","message":"One sentence motivational tip"},'
            '"exercises":['
            '{"name":"Exercise name","sets":3,"reps":12,"rest_seconds":30,"instructions":"Step by step instructions","benefits":"What this improves"},'
            '{"name":"Exercise name","sets":3,"reps":12,"rest_seconds":30,"instructions":"Step by step instructions","benefits":"What this improves"},'
            '{"name":"Exercise name","sets":3,"reps":12,"rest_seconds":30,"instructions":"Step by step instructions","benefits":"What this improves"},'
            '{"name":"Exercise name","sets":3,"reps":12,"rest_seconds":30,"instructions":"Step by step instructions","benefits":"What this improves"},'
            '{"name":"Exercise name","sets":3,"reps":12,"rest_seconds":30,"instructions":"Step by step instructions","benefits":"What this improves"},'
            '{"name":"Exercise name","sets":3,"reps":12,"rest_seconds":30,"instructions":"Step by step instructions","benefits":"What this improves"}'
            ']}}'
        )

        last_error = None
        cleaned = ""

        for attempt in range(1, 4):
            try:
                logger.info(f"Workout AI attempt {attempt}/3 for focus={focus.value}")

                response = genai.GenerativeModel(settings.GEMINI_MODEL).generate_content(
                    prompt,
                    generation_config=genai.GenerationConfig(
                        temperature=0.3,
                        max_output_tokens=4000,
                    )
                )

                raw = getattr(response, 'text', '') or ''
                if not raw.strip():
                    last_error = ValueError("Empty response")
                    logger.warning(f"Attempt {attempt}: empty response")
                    continue

                logger.info(f"Attempt {attempt} raw response (first 300): {raw[:300]}")

                cleaned = _clean_json_response(raw)
                cleaned = _sanitize_json_text(cleaned)
                workout_data = json.loads(cleaned)
                workout_data["generated_at"] = datetime.now(timezone.utc).isoformat()
                logger.info(f"Workout plan generated on attempt {attempt}")
                return workout_data

            except json.JSONDecodeError as e:
                last_error = e
                logger.warning(f"Attempt {attempt} JSON parse error: {e}")
                logger.warning(f"Attempt {attempt} cleaned text (first 500): {cleaned[:500]}")
                continue
            except Exception as e:
                logger.error(f"Error generating workout plan: {e}")
                raise

        logger.error(f"All 3 attempts failed. Last error: {last_error}")
        raise ValueError("AI generated invalid workout plan format")
        
        