import json
from datetime import datetime, timezone

import google.generativeai as genai

from app.core.config import settings
from app.core.logging import logger
from app.schemas.workout import WorkoutFocus

genai.configure(api_key=settings.GEMINI_API_KEY)
model = genai.GenerativeModel(settings.GEMINI_MODEL)


class WorkoutAIService:

    @staticmethod
    def generate_workout_plan(
        focus: WorkoutFocus,
        user_data: dict,
        intensity: str = "moderate",
        duration_minutes: int = 30,
    ) -> dict:
        prompt = f"""
You are a professional fitness coach creating a personalized workout plan.

USER PROFILE:
- Age: {user_data.get('age', 'Not specified')}
- Gender: {user_data.get('gender', 'Not specified')}
- Fitness Level: {user_data.get('fitness_level', 'beginner')}
- Workout Frequency: {user_data.get('workout_frequency', '3 times per week')}
- Equipment Available: {user_data.get('equipment', 'None')}
- Goals: {user_data.get('goals', 'General fitness')}

WORKOUT REQUIREMENTS:
- Focus Area: {focus.value.replace('_', ' ').title()}
- Intensity: {intensity.title()}
- Target Duration: {duration_minutes} minutes
- Exercise Count: 6 exercises

Generate a workout plan as a JSON object with this EXACT structure:
{{
  "focus": "{focus.value}",
  "title": "Short catchy title",
  "description": "One-line motivational description",
  "duration_minutes": {duration_minutes},
  "exercise_count": 6,
  "intensity": "{intensity}",
  "insight": {{
    "title": "Short insight title",
    "message": "Motivational message about consistency and benefits"
  }},
  "exercises": [
    {{
      "name": "Exercise name",
      "duration_seconds": 180,
      "sets": null,
      "reps": null,
      "rest_seconds": 30,
      "instructions": "Clear, concise instructions (1-2 sentences)",
      "benefits": "What this exercise improves",
      "difficulty": "beginner/intermediate/advanced"
    }}
  ]
}}

Rules:
1. Mix time-based and rep-based exercises appropriately
2. Start with a warm-up, end with a cool-down/stretch
3. Progress from easier to harder exercises
4. Ensure exercises match the focus area
5. Return ONLY valid JSON, no markdown or extra text
"""

        try:
            response = model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(temperature=0.7, max_output_tokens=2000)
            )

            response_text = response.text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]

            workout_data = json.loads(response_text.strip())
            workout_data["generated_at"] = datetime.now(timezone.utc).isoformat()

            logger.info(f"Generated workout plan for focus: {focus.value}")
            return workout_data

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI workout response: {e}")
            raise ValueError("AI generated invalid workout plan format")
        except Exception as e:
            logger.error(f"Error generating workout plan: {e}")
            raise

