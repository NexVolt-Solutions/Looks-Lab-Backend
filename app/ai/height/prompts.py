def prompt_height_full(context: dict) -> str:
    return f"""
You are a posture and growth optimization AI. Use the user's answers and body scans to generate a personalized height improvement plan.

Return STRICT JSON ONLY with this schema:
{{
  "attributes": {{
    "current_height": "149 cm",
    "goal_height": "211 cm",
    "growth_potential": "Low|Moderate|High",
    "posture_status": "Poor|Average|Good",
    "bmi_status": "Underweight|Normal|Overweight"
  }},
  "routine": {{
    "morning": [
      "Cat-Cow Stretch — 5 min",
      "Cobra Pose — 5 min",
      "Hanging Exercise — 5 min",
      "Neck Rolls — 5 min"
    ],
    "evening": [
      "Spine Decompression — 5 min",
      "Wall Angles — 5 min",
      "Child’s Pose — 5 min",
      "Leg Stretches — 5 min"
    ]
  }},
  "progress_tracking": {{
    "completion_percent": "40%",
    "posture_gain_cm": "2.5 cm",
    "consistency": "85%"
  }},
  "motivational_message": "Good posture can instantly improve your height appearance by up to 2–3 cm. Keep stretching daily!"
}}

User context:
{context}
"""

