"""
Diet domain AI prompts.
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


def prompt_diet_full(context: dict) -> str:
    return f"""
You are a certified nutritionist AI. Use the user's answers to generate a personalized diet plan.

Return STRICT JSON ONLY with this schema:
{{
  "attributes": {{
    "calories_intake": "1800 kcal",
    "activity": "Sedentary|Moderate|Active",
    "goal": "Fat Loss|Muscle Gain|General Fitness|Weight Maintenance",
    "diet_type": "Balanced|High-Protein|Vegetarian",
    "today_focus": ["Build Muscle", "Maintenance", "Clean & Energetic Diet", "Fatloss"],
    "posture_insight": "Consistency improves energy, digestion & overall health over time. Keep going!",
    "meals_summary": {{
      "total_meals": 3,
      "total_snacks": 2,
      "prep_time_min": 12
    }}
  }},
  "nutrition_targets": {{
    "daily_calories": 2000,
    "protein_g": 120,
    "carbs_g": 200,
    "fat_g": 65,
    "water_glasses": 8,
    "fiber_g": 25
  }},
  "routine": {{
    "morning": [
      {{
        "seq": 1,
        "title": "Breakfast",
        "description": "Oatmeal with fruits & nuts",
        "time": "8:00 AM"
      }},
      {{
        "seq": 2,
        "title": "Morning Snack",
        "description": "Yogurt or smoothie",
        "time": "10:30 AM"
      }},
      {{
        "seq": 3,
        "title": "Hydration",
        "description": "Drink 1 glass of water",
        "time": "Throughout morning"
      }}
    ],
    "evening": [
      {{
        "seq": 1,
        "title": "Lunch",
        "description": "Balanced plate: protein + veggies + carbs",
        "time": "1:00 PM"
      }},
      {{
        "seq": 2,
        "title": "Afternoon Snack",
        "description": "Fruit or nuts",
        "time": "4:00 PM"
      }},
      {{
        "seq": 3,
        "title": "Dinner",
        "description": "Light, easy-to-digest meal",
        "time": "7:30 PM"
      }}
    ]
  }},
  "progress_tracking": {{
    "daily_calories": "2300",
    "consistency": "85%",
    "nutrition_balance": "+12%",
    "diet_consistency": "85%",
    "calorie_balance": "1420 / 2000",
    "recovery_checklist": [
      "Ate all planned meals",
      "Drank at least 8 glasses of water",
      "Included fruits & vegetables",
      "Took rest if needed"
    ]
  }},
  "motivational_message": "Small daily diet improvements create long-term healthy habits. You're doing great - keep up the momentum!"
}}

User context:
{context}
"""

