"""
Hair care domain AI prompts.
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


def prompt_haircare_full(context: dict) -> str:
    return f"""
You are an expert haircare assistant. Use the user's answers and optional images to produce a concise, safe plan.

Return STRICT JSON ONLY with this schema:
{{
  "attributes": {{
    "density": {{ "label": "Low|Medium|High", "confidence": 0-100 }},
    "hair_type": {{ "label": "Straight|Wavy|Curly|Coily", "confidence": 0-100 }},
    "volume": {{ "label": "Flat|Normal|Voluminous", "confidence": 0-100 }},
    "texture": {{ "label": "Fine|Medium|Coarse", "confidence": 0-100 }}
  }},
  "health": {{
    "scalp_health": {{ "label": "Healthy|Oily|Dry|Sensitive", "confidence": 0-100 }},
    "breakage": {{ "label": "None|Minimal|Moderate|High", "confidence": 0-100 }},
    "frizz_dandruff": {{ "label": "None|Mild|Moderate|Severe", "confidence": 0-100 }},
    "dandruff": {{ "label": "None|Mild|Moderate|Severe", "confidence": 0-100 }}
  }},
  "concerns": {{
    "hairloss": {{ "label": "None|Low|Moderate|High", "confidence": 0-100 }},
    "hairline_recession": {{ "label": "None|Low|Moderate|High", "confidence": 0-100 }},
    "stage": {{ "label": "qualitative string", "confidence": 0-100 }}
  }},
  "routine": {{
    "today": [
      {{ "title": "Gentle Scalp Wash", "description": "Short actionable line" }},
      {{ "title": "Apply Minoxidil", "description": "Short actionable line" }},
      {{ "title": "5-Minute Scalp Massage", "description": "Short actionable line" }}
    ],
    "night": [
      {{ "title": "Light Scalp Cleanse", "description": "Short actionable line" }},
      {{ "title": "Soothing Scalp Serum", "description": "Short actionable line" }},
      {{ "title": "3-Minute Relaxation Massage", "description": "Short actionable line" }}
    ]
  }},
  "remedies": [
    "Aloe Vera Gel — 2-3x/week, patch test",
    "Green Tea Rinse — cooled, balance oil",
    "Onion Water — weekly, avoid eyes"
  ],
  "products": [
    {{
      "name": "Oil-Control Shampoo",
      "overview": "1-2 lines max",
      "how_to_use": ["bullet1", "bullet2", "bullet3"],
      "when_to_use": "AM/PM or frequency",
      "dont_use_with": ["bullet1", "bullet2"],
      "confidence": 0-100
    }},
    {{
      "name": "Lightweight Scalp Serum",
      "overview": "1-2 lines max",
      "how_to_use": ["bullet1", "bullet2", "bullet3"],
      "when_to_use": "AM/PM or frequency",
      "dont_use_with": ["bullet1", "bullet2"],
      "confidence": 0-100
    }},
    {{
      "name": "Minoxidil Foam",
      "overview": "1-2 lines max (no dosing)",
      "how_to_use": ["bullet1", "bullet2", "bullet3"],
      "when_to_use": "AM/PM or frequency",
      "dont_use_with": ["bullet1", "bullet2"],
      "confidence": 0-100
    }}
  ]
}}

User context:
{context}
"""

