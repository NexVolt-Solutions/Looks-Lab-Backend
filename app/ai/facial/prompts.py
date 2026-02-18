"""
Facial domain AI prompts.
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


def prompt_facial_full(context: dict) -> str:
    return f"""
You are a facial analysis and grooming AI. Use the user's answers and face scans to generate a personalized facial improvement plan.

Return STRICT JSON ONLY with this schema:
{{
  "attributes": {{
    "symmetry": "Mostly|Slightly asymmetrical|Noticeably asymmetrical",
    "jawline": "Soft/Rounded|Medium/Slightly Defined|Sharp/Strong",
    "cheekbones": "Low/Flat|Medium/Normal|High/Prominent",
    "habits": "Low/Flat|Medium/Normal|High/Prominent",
    "feature_goal": "Sharper jawline|Defined cheekbones|Skin texture & tone",
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
        "Chin lift",
        "Jaw massage (thumb & index finger, left to right)",
        "Cheek puff transfer (right to left)",
        "Vowel stretch (O → E)",
        "Neck slide (forward & back)"
      ]
    }},
    {{
      "seq": 2,
      "title": "Lip Plumping",
      "duration": "2 min",
      "steps": [
        "Lip pout & hold",
        "Thumb massage around lips (small circles)",
        "Air kiss stretch",
        "Lip press & release"
      ]
    }},
    {{
      "seq": 3,
      "title": "Cheek Lifts",
      "duration": "3 min",
      "steps": [
        "Smile wide & hold",
        "Fingers under cheekbones, gently lift upward",
        "Cheek puff side-to-side",
        "Jaw open & cheek stretch"
      ]
    }},
    {{
      "seq": 4,
      "title": "Eye Firming",
      "duration": "4 min",
      "steps": [
        "Place ring fingers on outer corners of eyes, gently press",
        "Slowly close eyes, hold 5 sec, then relax",
        "Circular massage around eye sockets (light pressure)",
        "Lift eyebrows with fingers while keeping eyes closed"
      ]
    }},
    {{
      "seq": 5,
      "title": "Face Yoga Flow",
      "duration": "10 min",
      "steps": [
        "Forehead stretch: Place palms on forehead, gently push skin up, hold 5 sec",
        "Eyebrow lift: Use index fingers to lift brows while frowning lightly",
        "Cheek sculpt: Smile widely, press palms on cheeks, hold 5 sec",
        "Jaw release: Open mouth wide, gently massage jawline with thumbs",
        "Chin press: Tilt head back, press chin upwards with palms, hold 5 sec",
        "Lip stretch: Pucker lips, move side to side slowly",
        "Eye opener: Place fingers under eyes, gently lift while squinting",
        "Neck lengthener: Tilt head side to side, hold 5 sec each",
        "Cheek puff: Puff cheeks, move air left to right",
        "Relaxation: Place hands on face, breathe deeply, release tension"
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
      "Did lips/eyes exercises"
    ]
  }},
  "motivational_message": "Small daily facial exercises create noticeable long-term improvements. Keep going!"
}}

User context:
{context}
"""

