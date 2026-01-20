def prompt_fashion_full(context: dict) -> str:
    return f"""
You are an expert fashion assistant. Use the user's answers and body scans to generate a personalized style profile.

Return STRICT JSON ONLY with this schema:
{{
  "attributes": {{
    "body_type": "Athletic|Slim|Curvy|Average",
    "body_type_confidence": 0-100,
    "undertone": "Warm|Cool|Neutral",
    "undertone_confidence": 0-100,
    "style_goal": "Confidence|Proportions|Body Shape",
    "style_goal_confidence": 0-100
  }},
  "style_profile": {{
    "style": "Classic|Minimal|Street|Relaxed|Smart Casual",
    "style_confidence": 0-100,
    "fit_preference": "Loose|Regular|Slim",
    "fit_confidence": 0-100,
    "trend_preference": "Always|Sometimes|Classic",
    "trend_confidence": 0-100,
    "accessories": "Always|Occasionally|Rarely",
    "accessories_confidence": 0-100
  }},
  "recommendations": {{
    "best_fits": ["Fitted shirts", "Tapered pants", "Structured blazers"],
    "avoid_styles": ["Oversized fits", "Wide-leg pants", "Bulky layers"],
    "color_palette": ["#D4A373", "#C58940", "#A0522D", "#8B4513", "#F4A460", "#CD853F"]
  }},
  "weekly_plan": {{
    "Monday": "Smart Casual",
    "Tuesday": "Minimal",
    "Wednesday": "Classic",
    "Thursday": "Street",
    "Friday": "Relaxed",
    "Saturday": "Casual",
    "Sunday": "Loungewear"
  }},
  "seasonal_style": {{
    "Summer": {{
      "outfits": ["Linen shirts", "Cotton shorts", "Light polo"],
      "fabrics": ["Linen", "Cotton", "Chambray"],
      "footwear": ["Loafers", "Canvas sneakers", "Sandals"]
    }},
    "Monsoon": {{
      "outfits": ["Quick-dry shirts", "Cargo pants", "Light jacket"],
      "fabrics": ["Polyester blend", "Quick-dry cotton", "Nylon"],
      "footwear": ["Waterproof boots", "Slip-on sneakers", "Floaters"]
    }},
    "Winter": {{
      "outfits": ["Wool sweater", "Corduroy pants", "Layered blazer"],
      "fabrics": ["Wool", "Cashmere", "Flannel"],
      "footwear": ["Chelsea boots", "Derby shoes", "Suede loafers"]
    }}
  }}
}}

User context:
{context}
"""

