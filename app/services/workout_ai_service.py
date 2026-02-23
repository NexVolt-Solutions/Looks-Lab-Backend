"""Workout AI service for generating personalized workout plans."""
import google.generativeai as genai
import json
from datetime import datetime, timezone

from app.core.config import settings
from app.core.logging import logger
from app.schemas.workout import WorkoutFocus

# Configure Gemini
genai.configure(api_key=settings.GEMINI_API_KEY)
model = genai.GenerativeModel(settings.GEMINI_MODEL)


class WorkoutAIService:
    """Service for generating AI-powered workout plans."""

    @staticmethod
    def generate_workout_plan(
        focus: WorkoutFocus,
        user_data: dict,
        intensity: str = "moderate",
        duration_minutes: int = 30,
    ) -> dict:
        """
        Generate personalized workout plan using Gemini AI.

        Args:
            focus: Workout focus area
            user_data: User profile and answers
            intensity: Workout intensity level
            duration_minutes: Target workout duration

        Returns:
            Structured workout plan with exercises
        """
        # Build prompt
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

Please generate a workout plan as a JSON object with this EXACT structure:
{{
  "focus": "{focus.value}",
  "title": "Short catchy title (e.g., 'Flexibility Focus Workout')",
  "description": "One-line motivational description",
  "duration_minutes": {duration_minutes},
  "exercise_count": 6,
  "intensity": "{intensity}",
  "insight": {{
    "title": "Short insight title (e.g., 'Posture Insight')",
    "message": "Motivational message about consistency and benefits"
  }},
  "exercises": [
    {{
      "name": "Exercise name",
      "duration_seconds": 180 or null (if reps-based),
      "sets": 3 or null (if duration-based),
      "reps": 12 or null (if duration-based),
      "rest_seconds": 30,
      "instructions": "Clear, concise instructions",
      "benefits": "What this exercise improves",
      "difficulty": "beginner/intermediate/advanced"
    }}
    // ... 5 more exercises
  ]
}}

IMPORTANT:
1. Mix time-based and rep-based exercises appropriately
2. Include proper warm-up exercise first
3. Progress from easier to harder exercises
4. Include cool-down/stretch at the end
5. Ensure exercises match the focus area
6. Keep instructions concise (1-2 sentences)
7. Return ONLY valid JSON, no markdown or extra text
"""

        try:
            # Generate with Gemini
            response = model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=2000,
                )
            )

            # Extract JSON from response
            response_text = response.text.strip()

            # Remove markdown code blocks if present
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]

            response_text = response_text.strip()

            # Parse JSON
            workout_data = json.loads(response_text)

            # Add timestamp
            workout_data["generated_at"] = datetime.now(timezone.utc).isoformat()

            logger.info(f"Generated workout plan for focus: {focus.value}")
            return workout_data

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            logger.error(f"Response text: {response_text}")
            raise ValueError("AI generated invalid workout plan format")

        except Exception as e:
            logger.error(f"Error generating workout plan: {e}")
            raise

