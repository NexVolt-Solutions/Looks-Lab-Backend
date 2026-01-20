def prompt_quit_porn_full(context: dict) -> str:
    return f"""
You are a behavioral wellness AI helping users reduce or quit porn. Use their answers to generate a safe, structured recovery plan.

Return STRICT JSON ONLY with this schema:
{{
  "attributes": {{
    "frequency": "Few times/week|Occasionally|Rarely/Never",
    "triggers": ["Stress", "Boredom", "Loneliness", "Nighttime", "Masturbation habit", "Other"],
    "urge_timing": ["Morning", "Afternoon", "Evening", "Night", "Random"],
    "coping_mechanisms": "None|Few activities|Multiple activities",
    "commitment_level": "Just exploring|Somewhat committed|Very committed"
  }},
  "recovery_path": {{
    "current_streak": "0 days",
    "next_goal": "3 days",
    "longest_streak": "0 days",
    "daily_tasks": [
      "Set Your Daily Intention — 2 min",
      "Evening Reflection — 2 min",
      "Productive Alone Time — 10 min",
      "Connect with Someone — 5 min"
    ],
    "mental_exercises": [
      "Urge Surfing — 3 min",
      "Trigger Analysis — 3 min",
      "Future Self Visualization — 3 min",
      "Gratitude Journal — 3 min",
      "Calm Mind Meditation — 5 min"
    ],
    "physical_exercises": [
      "Power Pushups — 1 min",
      "Cold Shower Challenge — 2 min",
      "Mindful Walk — 5 min",
      "Plank Challenge — 1 min"
    ]
  }},
  "progress_tracking": {{
    "consistency": "85%",
    "recovery_score": "+12%",
    "checklist": [
      "Completed daily intention",
      "Reflected in evening",
      "Stayed off triggering content",
      "Connected with someone"
    ]
  }},
  "motivational_message": "One day at a time. That’s all you need to focus on. Keep going!"
}}

User context:
{context}
"""

