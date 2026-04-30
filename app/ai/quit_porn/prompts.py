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


def prompt_quit_porn_full(context: dict) -> str:
    return f"""
You are a behavioral wellness AI helping users reduce or quit porn. Use their answers to generate a safe, structured recovery plan.

Important instructions:
- Return STRICT JSON ONLY.
- Do not include markdown, code fences, or any explanatory text outside the JSON object.
- Keep the tone supportive, practical, and non-judgmental.
- Daily tasks should be short, achievable, and realistic.
- Recovery suggestions should focus on healthy habits, reflection, connection, and urge management.

Return this JSON schema exactly:
{{
  "attributes": {{
    "frequency": "Few times/week|Occasionally|Rarely/Never",
    "triggers": ["Stress / anxiety", "Boredom", "Loneliness", "Nighttime / before sleep", "Habit loop", "Other"],
    "urge_timing": ["Morning", "Afternoon", "Evening", "Night", "Random / anytime"],
    "coping_mechanisms": "None|Few activities|Yes, multiple activities",
    "commitment_level": "Just exploring|Somewhat committed|Very committed"
  }},
  "recovery_path": {{
    "streak": {{
      "current_streak": 0,
      "longest_streak": 0,
      "next_goal": 7,
      "streak_message": "Today is day one. Let's make it count!"
    }},
    "daily_tasks": [
      {{
        "id": "task_1",
        "seq": 1,
        "order": 1,
        "title": "Set Your Daily Intention",
        "description": "One short sentence describing the task.",
        "duration": "2 min",
        "duration_min": 2,
        "completed": false
      }},
      {{
        "id": "task_2",
        "seq": 2,
        "order": 2,
        "title": "Evening Reflection",
        "description": "One short sentence describing the task.",
        "duration": "5 min",
        "duration_min": 5,
        "completed": false
      }},
      {{
        "id": "task_3",
        "seq": 3,
        "order": 3,
        "title": "Productive Alone Time",
        "description": "One short sentence describing the task.",
        "duration": "5 min",
        "duration_min": 5,
        "completed": false
      }},
      {{
        "id": "task_4",
        "seq": 4,
        "order": 4,
        "title": "Connect with Someone",
        "description": "One short sentence describing the task.",
        "duration": "10 min",
        "duration_min": 10,
        "completed": false
      }}
    ]
  }},
  "progress_tracking": {{
    "consistency": "42%",
    "recovery_score": "58%",
    "recovery_checklist": [
      "Set your daily intention",
      "Evening reflection",
      "Productive alone time",
      "Connect with someone"
    ]
  }},
  "motivational_message": "One short encouraging sentence."
}}

User context:
{context}
"""
