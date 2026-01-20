from app.ai.height.prompts import prompt_height_full

def build_context(answers: list[dict], images: list[dict]) -> dict:
    return {
        "answers": [{"step": a.get("step"), "question": a.get("question"), "answer": a.get("answer")} for a in answers],
        "images": [{"view": i.get("view"), "present": bool(i.get("url"))} for i in images],
    }

def analyze_height(answers: list[dict], images: list[dict]) -> dict:
    context = build_context(answers, images)
    prompt = prompt_height_full(context)
    # Call Gemini/OpenAI here and parse response
    return {
        "attributes": {},
        "routine": {},
        "progress_tracking": {},
        "motivational_message": ""
    }

