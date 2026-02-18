"""
Height domain AI prompts.
"""


def build_context(answers: list[dict], images: list[dict]) -> dict:
    return {
        "answers": [
            {
                "step": a.get("step"),
                "question": a.get("question"),
                "answer": a.get("answer")
            }
            for a in answers
        ],
        "images": [
            {
                "view": i.get("view"),
                "present": bool(i.get("url"))
            }
            for i in images
        ],
    }


def prompt_height_full(context: dict) -> str:
    return f"""
You are a posture and growth optimization AI. Use the user's answers to generate a personalized height improvement plan.

Return STRICT JSON ONLY with this schema:
{{
  "attributes": {{
    "current_height": "149 cm",
    "goal_height": "211 cm",
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
          "Come on all fours, hands under shoulders, knees under hips",
          "Inhale, drop belly, lift chest & chin (Cow)",
          "Exhale, round spine, tuck chin to chest (Cat)",
          "Move slowly with your breath",
          "Repeat in a smooth, controlled flow"
        ]
      }},
      {{
        "seq": 2,
        "title": "Cobra Pose",
        "duration": "5 min",
        "steps": [
          "Lie on your stomach, legs extended",
          "Place palms under shoulders",
          "Inhale and slowly lift chest up",
          "Keep hips on the floor, shoulders relaxed",
          "Hold briefly, then lower down gently"
        ]
      }},
      {{
        "seq": 3,
        "title": "Hanging Exercise",
        "duration": "5 min",
        "steps": [
          "Hold a pull-up bar with both hands",
          "Arms straight, body relaxed",
          "Let your body hang freely",
          "Keep shoulders loose, breathe normally",
          "Release slowly and rest if needed"
        ]
      }},
      {{
        "seq": 4,
        "title": "Neck Rolls",
        "duration": "5 min",
        "steps": [
          "Sit or stand straight",
          "Drop chin gently toward chest",
          "Slowly roll head to the right",
          "Move in a smooth circle",
          "Switch direction after a few rounds"
        ]
      }}
    ],
    "evening": [
      {{
        "seq": 1,
        "title": "Spine Decompression",
        "duration": "5 min",
        "steps": [
          "Lie on your back, knees bent",
          "Hug knees to chest gently",
          "Relax shoulders and neck",
          "Breathe deeply and hold",
          "Release slowly and repeat"
        ]
      }},
      {{
        "seq": 2,
        "title": "Wall Angles",
        "duration": "5 min",
        "steps": [
          "Stand with your back against a wall",
          "Keep head, shoulders, and lower back touching the wall",
          "Raise arms to shoulder height, elbows bent",
          "Slowly move arms up and down like wings",
          "Keep movements slow and controlled"
        ]
      }},
      {{
        "seq": 3,
        "title": "Child's Pose",
        "duration": "5 min",
        "steps": [
          "Kneel on the floor, big toes together",
          "Sit back on your heels",
          "Bend forward, arms stretched ahead",
          "Rest forehead on the mat",
          "Breathe deeply and relax"
        ]
      }},
      {{
        "seq": 4,
        "title": "Leg Stretches",
        "duration": "5 min",
        "steps": [
          "Sit or stand tall",
          "Stretch one leg at a time",
          "Reach toward toes gently",
          "Keep back straight, no bouncing",
          "Switch legs and repeat"
        ]
      }}
    ]
  }},
  "motivational_message": "Good posture can instantly improve your height appearance by up to 2-3 cm. Keep stretching daily!"
}}

User context:
{context}
"""

