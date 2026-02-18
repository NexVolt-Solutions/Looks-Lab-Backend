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
    "frizz_dryness": {{ "label": "None|Mild|Moderate|Severe", "confidence": 0-100 }},
    "dandruff": {{ "label": "None|Mild|Moderate|Severe", "confidence": 0-100 }}
  }},
  "concerns": {{
    "hairloss": {{ "label": "None|Low|Moderate|High", "confidence": 0-100 }},
    "hairline_recession": {{ "label": "None|Low|Moderate|High", "confidence": 0-100 }},
    "stage": {{ "label": "qualitative string", "confidence": 0-100 }}
  }},
  "routine": {{
    "today": [
      {{ "title": "Gentle Scalp Wash", "description": "Removes excess oil and buildup without drying the scalp. Helps maintain a clean and balanced scalp environment." }},
      {{ "title": "Apply Minoxidil", "description": "Stimulates hair follicles and supports healthy hair growth. Should be applied consistently as recommended by AI." }},
      {{ "title": "5-Minute Scalp Massage", "description": "Improves blood circulation to hair roots. Enhances nutrient delivery and reduces scalp tension." }}
    ],
    "night": [
      {{ "title": "Light Scalp Cleanse", "description": "Gently removes sweat and daily residue. Keeps scalp fresh without over-cleansing." }},
      {{ "title": "Apply Soothing Scalp Serum", "description": "Calms scalp irritation and supports overnight repair. Nourishes hair roots while you rest." }},
      {{ "title": "3-Minute Relaxation Massage", "description": "Relaxes scalp muscles and improves product absorption. Supports healthier hair growth over time." }}
    ]
  }},
  "remedies": [
    {{
      "name": "Aloe Vera Gel",
      "steps": [
        "Use 2-3 times/week",
        "Soothes scalp, reduces itchiness, controls oil"
      ]
    }},
    {{
      "name": "Green Tea Scalp Rinse",
      "steps": [
        "Prepare cooled green tea and rinse scalp",
        "Helps balance oil production and adds shine"
      ]
    }},
    {{
      "name": "Onion Water",
      "steps": [
        "Use once weekly",
        "Supports hair growth and scalp health"
      ]
    }}
  ],
  "safety_tips": [
    "Patch test before using new remedies",
    "Avoid contact with eyes",
    "Discontinue if irritation occurs"
  ],
  "products": [
    {{
      "name": "Oil-Control Shampoo",
      "tags": ["Product Buildup", "Oily Scalp", "Excess Sebum"],
      "time_of_day": "AM/PM",
      "overview": "1-2 lines describing what this product does and why it was AI-selected for this user.",
      "how_to_use": [
        "Use 2-3 times per week",
        "Apply to wet scalp and massage gently",
        "Rinse thoroughly",
        "Repeat if needed"
      ],
      "when_to_use": "AM or PM (during hair wash)",
      "dont_use_with": [
        "Harsh sulfate shampoos",
        "Overlapping medicated shampoos"
      ],
      "confidence": 0-100
    }},
    {{
      "name": "Lightweight Scalp Serum",
      "tags": ["Weak Roots", "Scalp Dryness", "Hair Thinning Support"],
      "time_of_day": "PM",
      "overview": "1-2 lines describing what this product does and why it was AI-selected for this user.",
      "how_to_use": [
        "Apply a few drops directly to the scalp",
        "Gently massage with fingertips",
        "Do not rinse"
      ],
      "when_to_use": "Daily (AM or PM)",
      "dont_use_with": [
        "Alcohol-based scalp products",
        "Heavy oils layer"
      ],
      "confidence": 0-100
    }},
    {{
      "name": "Minoxidil Foam",
      "tags": ["Hair Thinning", "Hair Fall", "Low Density Areas"],
      "time_of_day": "AM/PM",
      "overview": "1-2 lines describing what this product does and why it was AI-selected for this user.",
      "how_to_use": [
        "Apply to clean, dry scalp",
        "Use only on affected areas",
        "Wash hands after application"
      ],
      "when_to_use": "As recommended by AI (usually once or twice daily)",
      "dont_use_with": [
        "Heavy styling products immediately after"
      ],
      "confidence": 0-100
    }}
  ],
  "motivational_message": "Consistency is key — your scalp health will improve with daily care!"
}}

User context:
{context}
"""

