def build_context(answers: list[dict], images: list[dict]) -> dict:
    answer_map = {}
    for answer in answers:
        question = str(answer.get("question") or "").lower()
        value = answer.get("answer")
        if "accessor" in question:
            answer_map["accessories_preference"] = value
        elif "fashion trend" in question or "follow fashion" in question or "trend" in question:
            answer_map["trend_preference"] = value
        elif "clothes to fit" in question or "prefer your clothes" in question or "fit" in question:
            answer_map["fit_preference"] = value
        elif "active" in question or "activity" in question:
            answer_map["activity_level"] = value
        elif "style to highlight" in question or "style goal" in question:
            answer_map["style_goal"] = value

    return {
        "answer_map": answer_map,
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
- Weekly plan must include all 7 days from Monday to Sunday exactly once.
- Recommendations must align with user-selected preferences in answer_map.

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
