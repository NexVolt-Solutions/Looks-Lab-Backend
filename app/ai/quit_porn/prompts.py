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

Return STRICT JSON ONLY with this schema:
{{
  "attributes": {{
    "frequency": "Few times/week|Occasionally|Rarely/Never",
    "triggers": ["Stress / anxiety", "Boredom", "Loneliness", "Nighttime / before sleep", "Masturbation habit", "Other"],
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
        "description": "Take 2 minutes to write down your intention for today. Why do you want to stay clean?",
        "duration": "2 min",
        "duration_min": 2,
        "completed": false
      }},
      {{
        "id": "task_2",
        "seq": 2,
        "order": 2,
        "title": "Evening Reflection",
        "description": "Write 3 wins from today, no matter how small. Celebrate your progress.",
        "duration": "5 min",
        "duration_min": 5,
        "completed": false
      }},
      {{
        "id": "task_3",
        "seq": 3,
        "order": 3,
        "title": "Productive Alone Time",
        "description": "Plan something constructive for when you are alone. Read, exercise, learn, or create.",
        "duration": "5 min",
        "duration_min": 5,
        "completed": false
      }},
      {{
        "id": "task_4",
        "seq": 4,
        "order": 4,
        "title": "Connect with Someone",
        "description": "Text, call, or meet a friend or family member. Human connection is healing.",
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
  "motivational_message": "One day at a time. That is all you need to focus on. Keep going!"
}}

User context:
{context}
"""

