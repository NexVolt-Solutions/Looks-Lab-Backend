def prompt_workout_full(context: dict) -> str:
    return f"""
You are a certified fitness coach AI. Use the user's answers to generate a personalized workout plan.

Return STRICT JSON ONLY with this schema:
{{
  "attributes": {{
    "activity_level": "Sedentary|Moderate|Active",
    "hydration": "<1L|1–2L|>2L",
    "goal": "Fat loss|Muscle gain|Maintenance",
    "diet_type": "Balanced|High-Protein|Vegetarian",
    "focus_tags": ["Flexibility", "Build Muscle", "Fatloss", "Stamina"]
  }},
  "routine": {{
    "morning": [
      {{
        "name": "Jumping Jacks",
        "duration": "5 min",
        "instructions": "Stand straight, jump and spread legs while raising arms, return to start position. Maintain steady pace."
      }},
      {{
        "name": "Bodyweight Squats",
        "duration": "5 min",
        "instructions": "Feet shoulder-width apart, bend knees, lower hips, rise back up. Maintain proper form."
      }},
      {{
        "name": "Arm Circles",
        "duration": "2 min",
        "instructions": "Extend arms, rotate forward/backward in controlled circles. Keep shoulders relaxed."
      }}
    ],
    "evening": [
      {{
        "name": "Jumping Jacks",
        "duration": "5 min",
        "instructions": "Same as morning."
      }},
      {{
        "name": "Plank",
        "duration": "2 min",
        "instructions": "Forearm plank, body straight, engage core. Hold position, modify if needed."
      }},
      {{
        "name": "Stretching",
        "duration": "5 min",
        "instructions": "Overhead stretch, side bends, forward folds, shoulder rolls, neck tilts. Hold each for 15–30 sec."
      }}
    ]
  }},
  "progress_tracking": {{
    "weekly_calories": "230 kcal",
    "consistency": "85%",
    "strength_gain": "+12%",
    "recovery_checklist": [
      "Get 7+ hours of sleep",
      "Drink 8+ glasses of water",
      "Stretch/roll for 10 minutes",
      "Took rest if needed"
    ]
  }},
  "motivational_message": "Consistency improves stamina, strength & posture over time. Keep pushing!"
}}

User context:
{context}
"""

