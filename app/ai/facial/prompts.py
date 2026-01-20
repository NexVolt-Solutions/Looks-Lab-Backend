def prompt_facial_full(context: dict) -> str:
    return f"""
You are a facial analysis and grooming AI. Use the user's answers and face scans to generate a personalized improvement plan.

Return STRICT JSON ONLY with this schema:
{{
  "attributes": {{
    "symmetry": "Mostly|Slightly asymmetrical|Noticeably asymmetrical",
    "jawline": "Soft|Medium|Sharp",
    "cheekbones": "Low|Medium|High",
    "habits": "Low|Medium|High",
    "feature_goal": "Jawline|Cheekbones|Skin texture",
    "exercise_time": "5–10 min|10–15 min|15+ min"
  }},
  "feature_scores": {{
    "jawline": "78%",
    "cheekbones": "72%",
    "symmetry": "75%",
    "overall": "50%",
    "face_shape": "Diamond|Oval|Round|Square"
  }},
  "daily_exercises": [
    {{
      "name": "Jawline Tightener",
      "duration": "5 min",
      "steps": [
        "Chin lift",
        "Jaw massage (thumb & index finger)",
        "Cheek puff transfer",
        "Vowel stretch (O → E)",
        "Neck slide"
      ]
    }},
    {{
      "name": "Lip Plumping",
      "duration": "2 min",
      "steps": [
        "Lip pout & hold",
        "Thumb massage around lips",
        "Air kiss stretch",
        "Lip press & release"
      ]
    }},
    {{
      "name": "Cheek Lifts",
      "duration": "3 min",
      "steps": [
        "Smile wide & hold",
        "Lift cheeks with fingers",
        "Cheek puff side-to-side",
        "Jaw open & cheek stretch"
      ]
    }},
    {{
      "name": "Eye Firming",
      "duration": "4 min",
      "steps": [
        "Press outer corners",
        "Close eyes & hold",
        "Circular massage",
        "Lift eyebrows while eyes closed"
      ]
    }},
    {{
      "name": "Face Yoga Flow",
      "duration": "10 min",
      "steps": [
        "Forehead stretch",
        "Eyebrow lift",
        "Cheek sculpt",
        "Jaw release",
        "Chin press",
        "Lip stretch",
        "Eye opener",
        "Neck lengthener",
        "Cheek puff",
        "Relaxation"
      ]
    }}
  ],
  "progress_tracking": {{
    "consistency": "85%",
    "feature_improvement": {{
      "jawline": "78%",
      "cheekbones": "72%",
      "symmetry": "75%"
    }},
    "checklist": [
      "Jawline exercises",
      "Cheekbone exercises",
      "Lips/eyes exercises"
    ]
  }},
  "motivational_message": "Small daily facial exercises create noticeable long-term improvements. Keep going!"
}}

User context:
{context}
"""

