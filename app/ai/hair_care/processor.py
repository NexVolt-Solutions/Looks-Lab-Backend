from app.ai.gemini_client import run_gemini_json
from app.ai.hair_care.prompts import prompt_haircare_full, build_context



# ---------------------------
# Normalizers
# ---------------------------

def normalize_attributes(data: dict) -> dict:
    a = data.get("attributes", {}) or {}
    return {
        "density": {
            "label": a.get("density"),
            "confidence": a.get("density_confidence")
        },
        "hair_type": {
            "label": a.get("hair_type"),
            "confidence": a.get("hair_type_confidence")
        },
        "volume": {
            "label": a.get("volume"),
            "confidence": a.get("volume_confidence")
        },
        "texture": {
            "label": a.get("texture"),
            "confidence": a.get("texture_confidence")
        },
    }


def normalize_health(data: dict) -> dict:
    h = data.get("health", {}) or {}
    return {
        "scalp_health": {
            "label": h.get("scalp_health"),
            "confidence": h.get("scalp_health_confidence")
        },
        "breakage": {
            "label": h.get("breakage"),
            "confidence": h.get("breakage_confidence")
        },
        "frizz_dandruff": {
            "label": h.get("frizz_dandruff"),
            "confidence": h.get("frizz_dandruff_confidence")
        },
        "dandruff": {
            "label": h.get("dandruff"),
            "confidence": h.get("dandruff_confidence")
        },
    }


def normalize_concerns(data: dict) -> dict:
    c = data.get("concerns", {}) or {}
    return {
        "hairloss": {
            "label": c.get("hairloss"),
            "confidence": c.get("hairloss_confidence")
        },
        "hairline_recession": {
            "label": c.get("hairline_recession"),
            "confidence": c.get("hairline_recession_confidence")
        },
        "stage": {
            "label": c.get("stage"),
            "confidence": c.get("stage_confidence")
        },
    }


def normalize_routine(data: dict) -> dict:
    r = data.get("routine", {}) or {}
    return {
        "today": r.get("today") or [],
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

def analyze_haircare(answers: list, images: list) -> dict:
    """
    Run Gemini AI analysis for haircare domain and normalize the output.
    """
    context = build_context(answers, images)
    prompt = prompt_haircare_full(context)

    raw = run_gemini_json(prompt, domain="haircare")

    return {
        "attributes": normalize_attributes(raw),
        "health": normalize_health(raw),
        "concerns": normalize_concerns(raw),
        "routine": normalize_routine(raw),
        "remedies": normalize_remedies(raw),
        "products": normalize_products(raw),
    }

