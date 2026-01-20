from app.ai.quit_porn.prompts import prompt_quit_porn_full

def build_context(answers: list[dict], images: list[dict]) -> dict:
    return {
        "answers": [{"step": a.get("step"), "question": a.get("question"), "answer": a.get("answer")} for a in answers],
        "images": []  # No image input for quit porn
    }

def analyze_quit_porn(answers: list[dict], images: list[dict]) -> dict:
    context = build_context(answers, images)
    prompt = prompt_quit_porn_full(context)
    # Call Gemini/OpenAI here and parse response
    return {
        "attributes": {},
        "recovery_path": {},
        "progress_tracking": {},
        "motivational_message": ""
    }

