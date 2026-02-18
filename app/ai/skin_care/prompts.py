"""
Skin care domain AI prompts.
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


def prompt_skincare_full(context: dict) -> str:
    return f"""
You are an expert skincare assistant. Use the user's answers and optional face image to produce a concise, safe skincare plan.

Return STRICT JSON ONLY with this schema:
{{
  "attributes": {{
    "skin_type": {{ "label": "Dry|Oily|Combination|Normal|Sensitive", "confidence": 0-100 }},
    "sensitivity": {{ "label": "Low|Moderate|High", "confidence": 0-100 }},
    "elasticity": {{ "label": "Low|Moderate|High", "confidence": 0-100 }},
    "oil_balance": {{ "label": "Low|Balanced|High", "confidence": 0-100 }},
    "hydration": {{ "label": "Weak|Moderate|Strong", "confidence": 0-100 }},
    "pore_visibility": {{ "label": "Low|Moderate|High", "confidence": 0-100 }}
  }},
  "health": {{
    "skin_health": {{ "label": "Healthy|Compromised|Damaged", "confidence": 0-100 }},
    "texture": {{ "label": "Smooth|Uneven|Rough", "confidence": 0-100 }},
    "skin_barrier": {{ "label": "Weak|Moderate|Strong", "confidence": 0-100 }},
    "smoothness": {{ "label": "Smooth|Rough|Very Rough", "confidence": 0-100 }},
    "brightness": {{ "label": "Bright|Dull|Very Dull", "confidence": 0-100 }}
  }},
  "concerns": {{
    "acne_breakouts": {{ "label": "None|Mild|Moderate|Severe", "confidence": 0-100 }},
    "pigmentation": {{ "label": "None|Low|Moderate|High", "confidence": 0-100 }},
    "darkness_spot": {{ "label": "None|Mild|Moderate|Severe", "confidence": 0-100 }},
    "wrinkles": {{ "label": "None|Mild|Noticeable|Severe", "confidence": 0-100 }},
    "uneven_tone": {{ "label": "None|Mild|Visible|Severe", "confidence": 0-100 }}
  }},
  "routine": {{
    "today": [
      {{
        "title": "Gentle Cleanser",
        "description": "Removes excess oil, sweat, and impurities without stripping natural moisture. Keeps skin fresh and balanced for the day."
      }},
      {{
        "title": "Oil-Control / Balancing Serum",
        "description": "Helps regulate sebum production and minimise shine. Improves skin texture and keeps pores clear."
      }},
      {{
        "title": "Lightweight Moisturizer",
        "description": "Provides essential hydration without feeling heavy or greasy. Supports skin barrier and all-day comfort."
      }}
    ],
    "night": [
      {{
        "title": "Deep Cleanse",
        "description": "Thoroughly removes dirt, oil, and buildup accumulated during the day. Prepares skin for nighttime repair."
      }},
      {{
        "title": "Night Moisturizer",
        "description": "Delivers deeper nourishment while skin regenerates during sleep. Helps improve softness and skin health overnight."
      }},
      {{
        "title": "2-Minute Facial Relaxation Massage",
        "description": "Boosts circulation and relieves facial tension. Supports relaxation and better product absorption."
      }}
    ]
  }},
  "remedies": [
    {{
      "name": "Aloe Vera Gel",
      "steps": [
        "Use 3-4 times/week",
        "Soothes skin, hydrates deeply, reduces redness"
      ]
    }},
    {{
      "name": "Honey & Yogurt Mask",
      "steps": [
        "Use 1-2 times/week",
        "Brightens skin and improves texture"
      ]
    }},
    {{
      "name": "Rose Water Toner",
      "steps": [
        "Use daily",
        "Balances oil and refreshes skin"
      ]
    }}
  ],
  "safety_tips": [
    "Patch test before using new remedies",
    "Avoid contact with eyes"
  ],
  "products": [
    {{
      "name": "Salicylic Acid 2% Solution",
      "tags": ["Acne", "Blackheads", "Oily Skin"],
      "time_of_day": "PM",
      "overview": "1-2 lines describing what this product does and why it was AI-selected for this user's skin concerns.",
      "how_to_use": [
        "Apply once daily in the evening (PM)",
        "Apply a small dot to targeted areas (nose, chin, forehead)",
        "Or apply a thin layer over the entire face if recommended by AI",
        "Do not rinse"
      ],
      "when_to_use": "Night Routine (PM)",
      "dont_use_with": [
        "Retinoids",
        "EUK 134",
        "Copper Peptides",
        "Direct Acids"
      ],
      "confidence": 0
    }},
    {{
      "name": "Niacinamide 10% + Zinc 1%",
      "tags": ["Large Pores", "Uneven Texture", "Oiliness"],
      "time_of_day": "AM/PM",
      "overview": "1-2 lines describing what this product does and why it was AI-selected for this user's skin concerns.",
      "how_to_use": [
        "Apply once or twice daily (AM and/or PM)",
        "After cleansing and toning, apply 2-3 drops to the entire face",
        "Gently pat until fully absorbed",
        "Use sunscreen during daytime"
      ],
      "when_to_use": "AM & PM",
      "dont_use_with": [
        "Retinoids",
        "Pure Vitamin C",
        "Strong exfoliating acids"
      ],
      "confidence": 0
    }},
    {{
      "name": "Hyaluronic Acid 2% + B5",
      "tags": ["Dryness", "Fine Lines", "Dehydration"],
      "time_of_day": "AM/PM",
      "overview": "1-2 lines describing what this product does and why it was AI-selected for this user's skin concerns.",
      "how_to_use": [
        "Apply twice daily",
        "Use on slightly damp skin",
        "Apply a few drops over face and neck",
        "Follow with moisturizer"
      ],
      "when_to_use": "AM & PM",
      "dont_use_with": [
        "Direct Acids",
        "EUK 134",
        "Pure Vitamin C",
        "Copper Peptides"
      ],
      "confidence": 0
    }}
  ],
  "motivational_message": "Consistency is key — your skin will thank you with a healthy glow!"
}}

User context:
{context}
"""

