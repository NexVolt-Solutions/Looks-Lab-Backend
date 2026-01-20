from app.ai.fashion.prompts import prompt_fashion_full

def build_context(answers: list[dict], images: list[dict]) -> dict:
    return {
        "answers": [{"step": a.get("step"), "question": a.get("question"), "answer": a.get("answer")} for a in answers],
        "images": [{"view": i.get("view"), "present": bool(i.get("url"))} for i in images],
    }

def analyze_fashion(answers: list[dict], images: list[dict]) -> dict:
    context = build_context(answers, images)
    prompt = prompt_fashion_full(context)
    # Call Gemini/OpenAI here and parse response
    # For now, return mock structure
    return {
        "attributes": {},
        "style_profile": {},
        "recommendations": {},
        "weekly_plan": {},
        "seasonal_style": {}
    }

