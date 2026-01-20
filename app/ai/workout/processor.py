from app.ai.workout.prompts import prompt_workout_full

def build_context(answers: list[dict], images: list[dict]) -> dict:
    return {
        "answers": [{"step": a.get("step"), "question": a.get("question"), "answer": a.get("answer")} for a in answers],
        "images": []  # No image input for workout
    }

def analyze_workout(answers: list[dict], images: list[dict]) -> dict:
    context = build_context(answers, images)
    prompt = prompt_workout_full(context)
    # Call Gemini/OpenAI here and parse response
    return {
        "attributes": {},
        "routine": {},
        "progress_tracking": {},
        "motivational_message": ""
    }

