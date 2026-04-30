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


def prompt_skincare_full(context: dict) -> str:
    return f"""
You are an expert skincare assistant. Use the user's answers and optional face images to produce a concise, safe, practical skincare plan.

Important instructions:
- If image metadata is present, use it only as supporting context and stay conservative.
- If no image is present, infer only from the user's answers.
- Return STRICT JSON ONLY.
- Do not include markdown, code fences, or any explanatory text outside the JSON object.
- Confidence values must be integers from 0 to 100.
- Keep routine steps short, actionable, and suitable for daily use.

Return this JSON schema exactly:
{{
  "attributes": {{
    "skin_type": {{ "label": "Dry|Oily|Combination|Normal|Sensitive", "confidence": 0 }},
    "sensitivity": {{ "label": "Low|Moderate|High", "confidence": 0 }},
    "elasticity": {{ "label": "Low|Moderate|High", "confidence": 0 }},
    "oil_balance": {{ "label": "Low|Balanced|High", "confidence": 0 }},
    "hydration": {{ "label": "Weak|Moderate|Strong", "confidence": 0 }},
    "pore_visibility": {{ "label": "Low|Moderate|High", "confidence": 0 }}
  }},
  "health": {{
    "skin_health": {{ "label": "Healthy|Compromised|Damaged", "confidence": 0 }},
    "texture": {{ "label": "Smooth|Uneven|Rough", "confidence": 0 }},
    "skin_barrier": {{ "label": "Weak|Moderate|Strong", "confidence": 0 }},
    "smoothness": {{ "label": "Smooth|Rough|Very Rough", "confidence": 0 }},
    "brightness": {{ "label": "Bright|Dull|Very Dull", "confidence": 0 }}
  }},
  "concerns": {{
    "acne_breakouts": {{ "label": "None|Mild|Moderate|Severe", "confidence": 0 }},
    "pigmentation": {{ "label": "None|Low|Moderate|High", "confidence": 0 }},
    "darkness_spot": {{ "label": "None|Mild|Moderate|Severe", "confidence": 0 }},
    "wrinkles": {{ "label": "None|Mild|Noticeable|Severe", "confidence": 0 }},
    "uneven_tone": {{ "label": "None|Mild|Visible|Severe", "confidence": 0 }}
  }},
  "routine": {{
    "today": [
      {{ "title": "Short step title", "description": "One clear sentence." }},
      {{ "title": "Short step title", "description": "One clear sentence." }},
      {{ "title": "Short step title", "description": "One clear sentence." }}
    ],
    "night": [
      {{ "title": "Short step title", "description": "One clear sentence." }},
      {{ "title": "Short step title", "description": "One clear sentence." }},
      {{ "title": "Short step title", "description": "One clear sentence." }}
    ]
  }},
  "remedies": [
    {{
      "name": "Remedy name",
      "steps": [
        "Short instruction",
        "Short benefit or follow-up"
      ]
    }}
  ],
  "safety_tips": [
    "Short safety tip",
    "Short safety tip"
  ],
  "products": [
    {{
      "name": "Product name",
      "tags": ["Tag 1", "Tag 2"],
      "time_of_day": "AM|PM|AM/PM",
      "overview": "1-2 short lines describing why this product fits the user.",
      "how_to_use": [
        "Short step",
        "Short step"
      ],
      "when_to_use": "Short timing note",
      "dont_use_with": ["Conflict 1"],
      "confidence": 0
    }}
  ],
  "motivational_message": "One short encouraging sentence."
}}

User context:
{context}
"""
