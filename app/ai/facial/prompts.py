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


def prompt_facial_full(context: dict) -> str:
    return f"""
You are a facial analysis and grooming AI. Use the user's answers and optional face-scan metadata to generate a personalized facial improvement plan.

Important instructions:
- If image metadata is present, use it only as supporting context and stay conservative.
- If no image is present, infer only from the user's answers.
- Return STRICT JSON ONLY.
- Do not include markdown, code fences, or any explanatory text outside the JSON object.
- Keep all scores as integers from 0 to 100.
- Keep exercises practical, safe, and easy to follow.

Return this JSON schema exactly:
{{
  "attributes": {{
    "symmetry": "Mostly|Slightly asymmetrical|Noticeably asymmetrical",
    "jawline": "Soft/Rounded|Medium/Slightly Defined|Sharp/Strong",
    "cheekbones": "Low/Flat|Medium/Normal|High/Prominent",
    "habits": "Low|Moderate|High",
    "feature_goal": "Sharper jawline|Defined cheekbones|Skin texture and tone|Overall improvement",
    "exercise_time": "5-10 minutes|10-15 minutes|15+ minutes"
  }},
  "feature_scores": {{
    "overall_score": 50,
    "features": [
      {{ "name": "Jawline", "label": "Narrow", "score": 78 }},
      {{ "name": "Nose", "label": "Straight", "score": 78 }},
      {{ "name": "Lips", "label": "Medium", "score": 78 }},
      {{ "name": "Cheek bones", "label": "High", "score": 78 }},
      {{ "name": "Eyes", "label": "Almond", "score": 78 }},
      {{ "name": "Ears", "label": "Proportional", "score": 78 }},
      {{ "name": "Face Shape", "label": "Diamond Face Shape", "score": 78 }}
    ]
  }},
  "daily_exercises": [
    {{
      "seq": 1,
      "title": "Jawline Tightener",
      "duration": "5 min",
      "steps": [
        "Short step",
        "Short step"
      ]
    }},
    {{
      "seq": 2,
      "title": "Lip Plumping",
      "duration": "2 min",
      "steps": [
        "Short step",
        "Short step"
      ]
    }},
    {{
      "seq": 3,
      "title": "Cheek Lifts",
      "duration": "3 min",
      "steps": [
        "Short step",
        "Short step"
      ]
    }},
    {{
      "seq": 4,
      "title": "Eye Firming",
      "duration": "4 min",
      "steps": [
        "Short step",
        "Short step"
      ]
    }},
    {{
      "seq": 5,
      "title": "Face Yoga Flow",
      "duration": "10 min",
      "steps": [
        "Short step",
        "Short step"
      ]
    }}
  ],
  "progress_tracking": {{
    "jawline_score": 78,
    "cheekbones_score": 72,
    "symmetry_score": 75,
    "consistency": "85%",
    "recovery_checklist": [
      "Did jawline exercises",
      "Did cheekbone exercises",
      "Did lips and eyes exercises"
    ]
  }},
  "motivational_message": "One short encouraging sentence."
}}

User context:
{context}
"""
