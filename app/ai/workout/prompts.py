"""
Workout domain AI prompts.
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
        "images": []
    }


def prompt_workout_full(context: dict) -> str:
    return f"""
You are a certified fitness coach AI. Use the user's answers to generate a personalized workout plan.

Return STRICT JSON ONLY with this schema:
{{
  "attributes": {{
    "intensity": "Low|Moderate|High",
    "activity": "Sedentary|Moderate|Active",
    "goal": "Fat Loss|Muscle Gain|General Fitness|Weight Maintenance",
    "diet_type": "Balanced|High-Protein|Vegetarian",
    "today_focus": ["Flexibility", "Build Muscle", "Fatloss", "Strength"],
    "posture_insight": "Consistency improves stamina, strength & metabolism over time. Keep pushing!",
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
          "Stand straight with feet together",
          "Jump and spread legs while raising arms",
          "Jump back to start position",
          "Keep a steady pace",
          "Breathe normally and stay relaxed"
        ]
      }},
      {{
        "seq": 2,
        "title": "Bodyweight Squats",
        "duration": "5 min",
        "steps": [
          "Stand with feet shoulder-width apart",
          "Keep chest up and back straight",
          "Bend knees and lower hips as if sitting on a chair",
          "Go as low as comfortable, then rise back up",
          "Repeat steadily, maintaining proper form",
          "Breathe in while lowering, out while rising"
        ]
      }},
      {{
        "seq": 3,
        "title": "Arm Circles",
        "duration": "2 min",
        "steps": [
          "Stand straight with feet shoulder-width apart",
          "Extend arms out to the sides at shoulder height",
          "Rotate arms forward in small controlled circles",
          "Gradually make the circles bigger",
          "After 1 minute, switch direction and rotate backward",
          "Keep shoulders relaxed and core engaged"
        ]
      }}
    ],
    "evening": [
      {{
        "seq": 1,
        "title": "Jumping Jacks",
        "duration": "5 min",
        "steps": [
          "Stand straight with feet together",
          "Jump and spread legs while raising arms",
          "Jump back to start position",
          "Keep a steady pace",
          "Breathe normally and stay relaxed"
        ]
      }},
      {{
        "seq": 2,
        "title": "Plank",
        "duration": "2 min",
        "steps": [
          "Start in a forearm plank position, elbows under shoulders",
          "Keep body in a straight line from head to heels",
          "Engage core, glutes, and legs",
          "Avoid letting hips sag or lift too high",
          "Breathe steadily and hold the position",
          "Modify by dropping knees if needed for comfort"
        ]
      }},
      {{
        "seq": 3,
        "title": "Stretching",
        "duration": "5 min",
        "steps": [
          "Reach arms overhead and stretch upward",
          "Side stretches: lean gently to left and right",
          "Forward fold: hinge at hips, reach toward toes",
          "Shoulder rolls: forward and backward",
          "Neck stretch: tilt head gently left, right, forward, back",
          "Hold each stretch for 15-30 seconds, breathe deeply"
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
  "motivational_message": "Consistency improves stamina, strength & posture over time. Keep pushing!"
}}

User context:
{context}
"""

