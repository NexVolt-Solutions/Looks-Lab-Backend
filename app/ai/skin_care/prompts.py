def build_context(answers: list[dict], images: list[dict]) -> dict:
    """
    answers: [{step: "hydration", question: "...", answer: "Low"}, ...]
    images: [{view: "front", url: "s3://..."}, ...]
    """
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


def prompt_skincare_full(context: dict) -> str:
    """
    Request STRICT JSON for attributes, health, concerns, routine, remedies, products.
    Includes confidence percentages for attributes, health, and concerns.
    Products no longer include image_url (handled statically).
    """
    return f"""
You are an expert skincare assistant. Use the user's answers and optional images to produce a concise, safe plan.

Return STRICT JSON ONLY with this schema:
{{
  "attributes": {{
    "skin_type": {{ "label": "Dry|Oily|Combination|Normal|Sensitive", "confidence": 0-100 }},
    "tone": {{ "label": "Fair|Medium|Olive|Dark", "confidence": 0-100 }},
    "sensitivity": {{ "label": "Low|Moderate|High", "confidence": 0-100 }},
    "hydration": {{ "label": "Low|Medium|High", "confidence": 0-100 }}
  }},
  "health": {{
    "acne": {{ "label": "None|Mild|Moderate|Severe", "confidence": 0-100 }},
    "dryness": {{ "label": "None|Mild|Moderate|Severe", "confidence": 0-100 }},
    "oiliness": {{ "label": "None|Mild|Moderate|Severe", "confidence": 0-100 }},
    "redness": {{ "label": "None|Mild|Moderate|Severe", "confidence": 0-100 }}
  }},
  "concerns": {{
    "wrinkles": {{ "label": "None|Mild|Moderate|Severe", "confidence": 0-100 }},
    "pigmentation": {{ "label": "None|Mild|Moderate|Severe", "confidence": 0-100 }},
    "dark_circles": {{ "label": "None|Mild|Moderate|Severe", "confidence": 0-100 }}
  }},
  "routine": {{
    "morning": [
      {{ "title": "Gentle Cleanser", "description": "Short actionable line" }},
      {{ "title": "Moisturizer", "description": "Short actionable line" }},
      {{ "title": "Sunscreen", "description": "Short actionable line" }}
    ],
    "night": [
      {{ "title": "Cleanser", "description": "Short actionable line" }},
      {{ "title": "Serum", "description": "Short actionable line" }},
      {{ "title": "Night Cream", "description": "Short actionable line" }}
    ]
  }},
  "remedies": [
    "Honey Mask — weekly, patch test",
    "Cucumber Slices — daily, reduce puffiness",
    "Aloe Vera Gel — 2-3x/week, soothing"
  ],
  "products": [
    {{
      "name": "Gentle Cleanser",
      "overview": "1-2 lines max",
      "how_to_use": ["bullet1", "bullet2"],
      "when_to_use": "AM/PM",
      "dont_use_with": ["bullet1"],
      "confidence": 0-100
    }},
    {{
      "name": "Hydrating Serum",
      "overview": "1-2 lines max",
      "how_to_use": ["bullet1", "bullet2"],
      "when_to_use": "PM",
      "dont_use_with": ["bullet1"],
      "confidence": 0-100
    }},
    {{
      "name": "Moisturizer",
      "overview": "1-2 lines max",
      "how_to_use": ["bullet1", "bullet2"],
      "when_to_use": "AM/PM",
      "dont_use_with": ["bullet1"],
      "confidence": 0-100
    }}
  ]
}}

User context:
{context}
"""

