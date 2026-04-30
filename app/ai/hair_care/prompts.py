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


def prompt_haircare_full(context: dict) -> str:
    return f"""
You are an expert haircare assistant. Use the user's answers and optional hair/scalp images to produce a concise, safe, practical plan.

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
    "density": {{ "label": "Low|Medium|High", "confidence": 0 }},
    "hair_type": {{ "label": "Straight|Wavy|Curly|Coily", "confidence": 0 }},
    "volume": {{ "label": "Flat|Normal|Voluminous", "confidence": 0 }},
    "texture": {{ "label": "Fine|Medium|Coarse", "confidence": 0 }}
  }},
  "health": {{
    "scalp_health": {{ "label": "Healthy|Oily|Dry|Sensitive", "confidence": 0 }},
    "breakage": {{ "label": "None|Minimal|Moderate|High", "confidence": 0 }},
    "frizz_dryness": {{ "label": "None|Mild|Moderate|Severe", "confidence": 0 }},
    "dandruff": {{ "label": "None|Mild|Moderate|Severe", "confidence": 0 }}
  }},
  "concerns": {{
    "hairloss": {{ "label": "None|Low|Moderate|High", "confidence": 0 }},
    "hairline_recession": {{ "label": "None|Low|Moderate|High", "confidence": 0 }},
    "stage": {{ "label": "qualitative string", "confidence": 0 }}
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
