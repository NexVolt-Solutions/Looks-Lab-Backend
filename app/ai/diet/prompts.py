def prompt_diet_full(context: dict) -> str:
    return f"""
You are a certified nutritionist AI. Use the user's answers and food scans to generate a personalized diet plan.

Return STRICT JSON ONLY with this schema:
{{
  "attributes": {{
    "diet_type": "Balanced|High-Protein|Vegetarian",
    "goal": "Fat loss|Muscle gain|Maintenance",
    "activity_level": "Sedentary|Moderate|Active",
    "hydration": "<1L|1–2L|>2L"
  }},
  "nutrition_summary": {{
    "calories": 1800,
    "protein": "120g",
    "carbs": "150g",
    "portion_size": "300g"
  }},
  "daily_routine": {{
    "morning": [
      "Breakfast: Oatmeal with fruits & nuts",
      "Snack: Yogurt or smoothie",
      "Hydration: 1 glass of water"
    ],
    "evening": [
      "Lunch: Balanced plate (protein + veggies + carbs)",
      "Snack: Fruit or nuts",
      "Dinner: Light, easy-to-digest meal"
    ]
  }},
  "progress_tracking": {{
    "calorie_balance": "1420 / 2000",
    "diet_consistency": "85%",
    "recovery_checklist": [
      "Ate all planned meals",
      "Drank 8+ glasses of water",
      "Included fruits & vegetables",
      "Took rest if needed"
    ]
  }},
  "motivational_message": "Small daily diet improvements create long-term healthy habits. You're doing great!"
}}

User context:
{context}
"""
