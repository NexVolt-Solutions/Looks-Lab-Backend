from app.ai.gemini_client import run_gemini_json
from app.ai.skin_care.prompts import prompt_skincare_full, build_context

# ---------------------------
# Normalizers
# ---------------------------

def normalize_attributes(data: dict) -> dict:
    a = data.get("attributes", {}) or {}
    return {
        "skin_type": {
            "label": a.get("skin_type"),
            "confidence": a.get("skin_type_confidence")
        },
        "tone": {
            "label": a.get("tone"),
            "confidence": a.get("tone_confidence")
        },
        "sensitivity": {
            "label": a.get("sensitivity"),
            "confidence": a.get("sensitivity_confidence")
        },
        "hydration": {
            "label": a.get("hydration"),
            "confidence": a.get("hydration_confidence")
        },
    }


def normalize_health(data: dict) -> dict:
    h = data.get("health", {}) or {}
    return {
        "acne": {
            "label": h.get("acne"),
            "confidence": h.get("acne_confidence")
        },
        "dryness": {
            "label": h.get("dryness"),
            "confidence": h.get("dryness_confidence")
        },
        "oiliness": {
            "label": h.get("oiliness"),
            "confidence": h.get("oiliness_confidence")
        },
        "redness": {
            "label": h.get("redness"),
            "confidence": h.get("redness_confidence")
        },
    }


def normalize_concerns(data: dict) -> dict:
    c = data.get("concerns", {}) or {}
    return {
        "wrinkles": {
            "label": c.get("wrinkles"),
            "confidence": c.get("wrinkles_confidence")
        },
        "pigmentation": {
            "label": c.get("pigmentation"),
            "confidence": c.get("pigmentation_confidence")
        },
        "dark_circles": {
            "label": c.get("dark_circles"),
            "confidence": c.get("dark_circles_confidence")
        },
    }


def normalize_routine(data: dict) -> dict:
    r = data.get("routine", {}) or {}
    return {
        "morning": r.get("morning") or [],
        "night": r.get("night") or [],
    }


def normalize_remedies(data: dict) -> list:
    return data.get("remedies") or []


def normalize_products(data: dict) -> list:
    products = data.get("products") or []
    out = []
    for p in products[:3]:  # limit to top 3
        out.append({
            "name": p.get("name"),
            "overview": p.get("overview"),
            "how_to_use": p.get("how_to_use") or [],
            "when_to_use": p.get("when_to_use"),
            "dont_use_with": p.get("dont_use_with") or [],
            "confidence": p.get("confidence")
        })
    return out


# ---------------------------
# Main entry point
# ---------------------------

def analyze_skincare(answers: list, images: list) -> dict:
    """
    Run Gemini AI analysis for skincare domain and normalize the output.
    """
    context = build_context(answers, images)
    prompt = prompt_skincare_full(context)

    raw = run_gemini_json(prompt, domain="skincare")

    return {
        "attributes": normalize_attributes(raw),
        "health": normalize_health(raw),
        "concerns": normalize_concerns(raw),
        "routine": normalize_routine(raw),
        "remedies": normalize_remedies(raw),
        "products": normalize_products(raw),
    }

