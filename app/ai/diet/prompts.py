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
        "images": [
            {
                "view": i.get("view"),
                "present": bool(i.get("url")),
            }
            for i in images
        ],
    }


def prompt_diet_full(context: dict) -> str:
    return f"""
You are a certified nutritionist AI. Use the user's answers and optional meal images to generate a personalized diet plan.

Important instructions:
- If image metadata is present, use it only as supporting context and stay conservative.
- If no image is present, infer only from the user's answers.
- Return STRICT JSON ONLY.
- Do not include markdown, code fences, or any explanatory text outside the JSON object.
- Keep the plan practical, realistic, and easy to follow in daily life.
- Use simple food suggestions, not extreme diets.

Return this JSON schema exactly:
{{
  "attributes": {{
    "calories_intake": "1800 kcal",
    "activity": "Sedentary|Moderate|Active",
    "goal": "Fat Loss|Muscle Gain|General Fitness|Weight Maintenance",
    "diet_type": "Balanced|High-Protein|Vegetarian|Low-Carb|Maintenance",
    "today_focus": ["Build Muscle", "Maintenance", "Clean & Energetic Diet", "Fatloss"],
    "posture_insight": "One short encouraging insight.",
    "meals_summary": {{
      "total_meals": 3,
      "total_snacks": 2,
      "prep_time_min": 22
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
        "subtitle": "Oatmeal with fruits and nuts",
        "description": "One clear sentence explaining the purpose of this step.",
        "duration": "10 min"
      }},
      {{
        "seq": 2,
        "title": "Morning Snack",
        "subtitle": "Yogurt or smoothie",
        "description": "One clear sentence explaining the purpose of this step.",
        "duration": "5 min"
      }},
      {{
        "seq": 3,
        "title": "Hydration",
        "subtitle": "Drink 1 glass of water",
        "description": "One clear sentence explaining the purpose of this step.",
        "duration": "1 min"
      }}
    ],
    "evening": [
      {{
        "seq": 1,
        "title": "Lunch",
        "subtitle": "Balanced plate with protein, vegetables, and carbs",
        "description": "One clear sentence explaining the purpose of this step.",
        "duration": "20 min"
      }},
      {{
        "seq": 2,
        "title": "Afternoon Snack",
        "subtitle": "Fruit or nuts",
        "description": "One clear sentence explaining the purpose of this step.",
        "duration": "5 min"
      }},
      {{
        "seq": 3,
        "title": "Dinner",
        "subtitle": "Light, easy-to-digest meal",
        "description": "One clear sentence explaining the purpose of this step.",
        "duration": "20 min"
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
      "Included fruits and vegetables",
      "Took rest if needed"
    ]
  }},
  "motivational_message": "One short encouraging sentence."
}}

User context:
{context}
"""
