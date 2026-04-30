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


def prompt_height_full(context: dict) -> str:
    return f"""
You are a posture and growth optimization AI. Use the user's answers to generate a personalized height improvement plan.

Important instructions:
- Return STRICT JSON ONLY.
- Do not include markdown, code fences, or any explanatory text outside the JSON object.
- Keep the plan realistic and safe.
- Focus on posture, consistency, sleep, recovery, and flexibility rather than unrealistic growth claims.
- Keep exercises simple and practical.

Return this JSON schema exactly:
{{
  "attributes": {{
    "current_height": "149 cm",
    "goal_height": "160 cm",
    "growth_potential": "Low|Moderate|High",
    "posture_status": "Poor|Average|Good",
    "bmi_status": "Underweight|Normal|Overweight"
  }},
  "progress_tracking": {{
    "completion_percent": "40%",
    "posture_gain_cm": "2.5 cm",
    "consistency": "85%"
  }},
  "today_focus": [
    {{
      "title": "Neck Stretches",
      "duration": "5 min exercise"
    }},
    {{
      "title": "Spine Alignment",
      "duration": "5 min exercise"
    }}
  ],
  "exercises": {{
    "morning": [
      {{
        "seq": 1,
        "title": "Cat-Cow Stretch",
        "duration": "5 min",
        "steps": [
          "Short step",
          "Short step"
        ]
      }},
      {{
        "seq": 2,
        "title": "Cobra Pose",
        "duration": "5 min",
        "steps": [
          "Short step",
          "Short step"
        ]
      }},
      {{
        "seq": 3,
        "title": "Hanging Exercise",
        "duration": "5 min",
        "steps": [
          "Short step",
          "Short step"
        ]
      }},
      {{
        "seq": 4,
        "title": "Neck Rolls",
        "duration": "5 min",
        "steps": [
          "Short step",
          "Short step"
        ]
      }}
    ],
    "evening": [
      {{
        "seq": 1,
        "title": "Spine Decompression",
        "duration": "5 min",
        "steps": [
          "Short step",
          "Short step"
        ]
      }},
      {{
        "seq": 2,
        "title": "Wall Angles",
        "duration": "5 min",
        "steps": [
          "Short step",
          "Short step"
        ]
      }},
      {{
        "seq": 3,
        "title": "Child's Pose",
        "duration": "5 min",
        "steps": [
          "Short step",
          "Short step"
        ]
      }},
      {{
        "seq": 4,
        "title": "Leg Stretches",
        "duration": "5 min",
        "steps": [
          "Short step",
          "Short step"
        ]
      }}
    ]
  }},
  "motivational_message": "One short encouraging sentence."
}}

User context:
{context}
"""
