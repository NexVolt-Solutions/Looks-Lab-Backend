def build_context(answers: list[dict], images: list[dict]) -> dict:
    return {
        "answers": [
            {
                "step": a.get("step"),
                "question": a.get("question"),
                "answer": a.get("answer"),
            }
            for a in answers
        ],
        "images": [],
    }


def prompt_workout_full(context: dict) -> str:
    return f"""
You are a certified fitness coach AI. Use the user's answers to generate a personalized workout plan.

Important instructions:
- Return STRICT JSON ONLY.
- Do not include markdown, code fences, or any explanatory text outside the JSON object.
- Keep the workout realistic, beginner-safe when needed, and easy to follow at home or in a gym.
- Keep exercise steps short and practical.
- Prefer clear titles, practical durations, and helpful recovery guidance.

Return this JSON schema exactly:
{{
  "attributes": {{
    "intensity": "Low|Moderate|High",
    "activity": "Sedentary|Moderate|Active",
    "goal": "Fat Loss|Muscle Gain|General Fitness|Strength|Mobility",
    "today_focus": ["Flexibility", "Build Muscle", "Fatloss", "Strength"],
    "posture_insight": {{
      "title": "Posture Insight",
      "message": "One short personalized insight."
    }},
    "workout_summary": {{
      "total_exercises": 6,
      "total_duration_min": 22
    }}
  }},
  "exercises": {{
    "morning": [
      {{
        "seq": 1,
        "title": "Jumping Jacks",
        "duration": "5 min",
        "steps": [
          "Short step",
          "Short step"
        ]
      }},
      {{
        "seq": 2,
        "title": "Bodyweight Squats",
        "duration": "5 min",
        "steps": [
          "Short step",
          "Short step"
        ]
      }},
      {{
        "seq": 3,
        "title": "Arm Circles",
        "duration": "2 min",
        "steps": [
          "Short step",
          "Short step"
        ]
      }}
    ],
    "evening": [
      {{
        "seq": 1,
        "title": "Brisk Walk or Warmup",
        "duration": "5 min",
        "steps": [
          "Short step",
          "Short step"
        ]
      }},
      {{
        "seq": 2,
        "title": "Plank",
        "duration": "2 min",
        "steps": [
          "Short step",
          "Short step"
        ]
      }},
      {{
        "seq": 3,
        "title": "Stretching",
        "duration": "5 min",
        "steps": [
          "Short step",
          "Short step"
        ]
      }}
    ]
  }},
  "progress_tracking": {{
    "weekly_calories": "2300",
    "consistency": "85%",
    "strength_gain": "+12%",
    "fitness_consistency": "85%",
    "recovery_checklist": [
      "Got 7+ hours of sleep",
      "Drank 8+ glasses of water",
      "Stretched for 10 minutes",
      "Took a rest if needed"
    ]
  }},
  "motivational_message": "One short encouraging sentence."
}}

User context:
{context}
"""
