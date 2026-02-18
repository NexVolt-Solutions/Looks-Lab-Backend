"""
Quit porn domain AI prompts.
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
        "seq": 1,
        "title": "Set Your Daily Intention",
        "description": "Take 2 minutes to write down your intention for today. Why do you want to stay clean?",
        "duration": "2 min",
        "completed": false
      }},
      {{
        "seq": 2,
        "title": "Evening Reflection",
        "description": "Write 3 wins from today, no matter how small. Celebrate your progress.",
        "duration": "30 min",
        "completed": false
      }},
      {{
        "seq": 3,
        "title": "Productive Alone Time",
        "description": "Plan something constructive for when you're alone. Read, exercise, learn, or create.",
        "duration": "5 min",
        "completed": false
      }},
      {{
        "seq": 4,
        "title": "Connect with Someone",
        "description": "Text, call, or meet a friend or family member. Human connection is healing.",
        "duration": "10 min",
        "completed": false
      }}
    ],
    "exercises": [
      {{
        "seq": 1,
        "title": "Power Pushups",
        "description": "Channel your energy into physical strength. Do as many pushups as you can when urge hits.",
        "category": "physical",
        "completed": false
      }},
      {{
        "seq": 2,
        "title": "Cold Shower Challenge",
        "description": "A 2-minute cold shower to reset your nervous system and build mental resilience.",
        "category": "physical",
        "completed": false
      }},
      {{
        "seq": 3,
        "title": "Box Breathing",
        "description": "Breathe in for 4 seconds, hold for 4, breathe out for 4, hold for 4. Repeat 5 times.",
        "category": "mental",
        "completed": false
      }},
      {{
        "seq": 4,
        "title": "Mindful Walk",
        "description": "Take a 10 minute walk, focusing on each step and your surroundings. Leave your phone behind.",
        "category": "physical",
        "completed": false
      }},
      {{
        "seq": 5,
        "title": "Gratitude Journal",
        "description": "Write down 3 things you're grateful for today and why they matter to you.",
        "category": "mental",
        "completed": false
      }},
      {{
        "seq": 6,
        "title": "Urge Surfing",
        "description": "Observe your urge like a wave. Notice where you feel it in your body. Watch it rise and fall without acting.",
        "category": "mental",
        "completed": false
      }},
      {{
        "seq": 7,
        "title": "Plank Challenge",
        "description": "Hold a plank position for as long as you can. Focus on your breathing and core strength.",
        "category": "physical",
        "completed": false
      }},
      {{
        "seq": 8,
        "title": "Calm Mind Meditation",
        "description": "Sit quietly, close your eyes, and focus on your breath. Let thoughts pass like clouds.",
        "category": "mental",
        "completed": false
      }},
      {{
        "seq": 9,
        "title": "Trigger Analysis",
        "description": "Write about what triggered you today. Identify patterns and plan how to avoid them.",
        "category": "mental",
        "completed": false
      }},
      {{
        "seq": 10,
        "title": "Future Self Visualization",
        "description": "Close your eyes and visualize the person you're becoming. See your future self, confident and free.",
        "category": "mental",
        "completed": false
      }}
    ]
  }},
  "progress_tracking": {{
    "consistency": "85%",
    "recovery_score": "+12%",
    "recovery_checklist": [
      "Completed daily intention",
      "Reflected in evening",
      "Stayed off triggering content",
      "Connected with someone"
    ]
  }},
  "motivational_message": "One day at a time. That's all you need to focus on. Keep going!"
}}

User context:
{context}
"""

