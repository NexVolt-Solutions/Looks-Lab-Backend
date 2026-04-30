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


def prompt_fashion_full(context: dict) -> str:
    return f"""
You are an expert fashion assistant. Use the user's answers and optional body-scan metadata to generate a personalized style profile.

Important instructions:
- If image metadata is present, use it only as supporting context and stay conservative.
- If no image is present, infer only from the user's answers.
- Return STRICT JSON ONLY.
- Do not include markdown, code fences, or any explanatory text outside the JSON object.
- Keep the style advice practical, wearable, and specific.
- Color values in warm_palette must be valid hex strings.

Return this JSON schema exactly:
{{
  "attributes": {{
    "body_type": "Athletic|Slim|Curvy|Average",
    "undertone": "Warm|Cool|Neutral",
    "style": "Classic|Minimal|Street|Relaxed|Smart Casual",
    "best_clothing_fits": ["Fitted shirts", "Tapered pants", "Structured blazers"],
    "styles_to_avoid": ["Oversized fits", "Wide-leg pants", "Bulky layers"],
    "warm_palette": ["#C8A882", "#8B7355", "#C0622F", "#4A6741", "#C8973C", "#A0522D"],
    "analyzing_insights": [
      "Athletic body structure",
      "Warm skin undertone",
      "Balanced proportions",
      "Best fit: Regular",
      "Strong everyday style"
    ]
  }},
  "weekly_plan": [
    {{ "day": "Monday", "theme": "Smart Casual" }},
    {{ "day": "Tuesday", "theme": "Minimal" }},
    {{ "day": "Wednesday", "theme": "Classic" }},
    {{ "day": "Thursday", "theme": "Street" }},
    {{ "day": "Friday", "theme": "Relaxed" }},
    {{ "day": "Saturday", "theme": "Casual" }},
    {{ "day": "Sunday", "theme": "Loungewear" }}
  ],
  "seasonal_style": {{
    "summer": {{
      "outfit_combinations": ["Linen shirt", "Tailored shorts", "Lightweight sneakers"],
      "recommended_fabrics": ["Linen", "Cotton", "Chambray"],
      "footwear": ["Loafers", "Canvas sneakers", "Sandals"]
    }},
    "monsoon": {{
      "outfit_combinations": ["Quick-dry shirt", "Tapered pants", "Light jacket"],
      "recommended_fabrics": ["Polyester blend", "Quick-dry cotton", "Nylon"],
      "footwear": ["Waterproof boots", "Slip-on sneakers", "Floaters"]
    }},
    "winter": {{
      "outfit_combinations": ["Wool sweater", "Corduroy pants", "Layered blazer"],
      "recommended_fabrics": ["Wool", "Cashmere", "Flannel"],
      "footwear": ["Chelsea boots", "Derby shoes", "Suede loafers"]
    }}
  }},
  "motivational_message": "One short encouraging sentence."
}}

User context:
{context}
"""
