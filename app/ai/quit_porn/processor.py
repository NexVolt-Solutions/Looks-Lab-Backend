"""
Quit porn domain AI processor.
Generates structured recovery plans for behavioral wellness.
"""
from typing import Any

from app.ai.gemini_client import run_gemini_json, GeminiError
from app.ai.quit_porn.prompts import prompt_quit_porn_full
from app.core.logging import logger


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
        "images": []
    }


def _get_safe_value(data: dict, key: str, default: Any = None) -> Any:
    return data.get(key, default) if data else default


def normalize_attributes(data: dict) -> dict[str, Any]:
    try:
        attributes = _get_safe_value(data, "attributes", {})

        triggers = attributes.get("triggers", [])
        urge_timing = attributes.get("urge_timing", [])

        if not isinstance(triggers, list):
            triggers = []
        if not isinstance(urge_timing, list):
            urge_timing = []

        return {
            "frequency": attributes.get("frequency", "Occasionally"),
            "triggers": triggers[:5],
            "urge_timing": urge_timing[:5],
            "coping_mechanisms": attributes.get("coping_mechanisms", "Few activities"),
            "commitment_level": attributes.get("commitment_level", "Somewhat committed"),
        }
    except Exception as e:
        logger.error(f"Error normalizing quit_porn attributes: {str(e)}")
        return {
            "frequency": "Occasionally",
            "triggers": [],
            "urge_timing": [],
            "coping_mechanisms": "Few activities",
            "commitment_level": "Somewhat committed",
        }


def normalize_recovery_path(data: dict) -> dict[str, Any]:
    try:
        recovery = _get_safe_value(data, "recovery_path", {})

        daily_tasks = recovery.get("daily_tasks", [])
        mental_exercises = recovery.get("mental_exercises", [])
        physical_exercises = recovery.get("physical_exercises", [])

        if not isinstance(daily_tasks, list):
            daily_tasks = []
        if not isinstance(mental_exercises, list):
            mental_exercises = []
        if not isinstance(physical_exercises, list):
            physical_exercises = []

        return {
            "current_streak": recovery.get("current_streak", "0 days"),
            "next_goal": recovery.get("next_goal", "3 days"),
            "longest_streak": recovery.get("longest_streak", "0 days"),
            "daily_tasks": daily_tasks[:5],
            "mental_exercises": mental_exercises[:5],
            "physical_exercises": physical_exercises[:5],
        }
    except Exception as e:
        logger.error(f"Error normalizing quit_porn recovery path: {str(e)}")
        return {
            "current_streak": "0 days",
            "next_goal": "3 days",
            "longest_streak": "0 days",
            "daily_tasks": [],
            "mental_exercises": [],
            "physical_exercises": [],
        }


def normalize_progress_tracking(data: dict) -> dict[str, Any]:
    try:
        progress = _get_safe_value(data, "progress_tracking", {})

        checklist = progress.get("checklist", [])
        if not isinstance(checklist, list):
            checklist = []

        return {
            "consistency": progress.get("consistency", "0%"),
            "recovery_score": progress.get("recovery_score", "0%"),
            "checklist": checklist[:5]
        }
    except Exception as e:
        logger.error(f"Error normalizing quit_porn progress tracking: {str(e)}")
        return {
            "consistency": "0%",
            "recovery_score": "0%",
            "checklist": []
        }


def analyze_quit_porn(answers: list[dict], images: list[dict]) -> dict[str, Any] | None:
    try:
        logger.info(f"Starting quit_porn analysis with {len(answers)} answers")

        context = build_context(answers, images)
        prompt = prompt_quit_porn_full(context)

        raw = run_gemini_json(prompt, domain="quit porn")

        if not raw:
            logger.warning("Empty response from Gemini for quit_porn analysis")
            return None

        normalized = {
            "attributes": normalize_attributes(raw),
            "recovery_path": normalize_recovery_path(raw),
            "progress_tracking": normalize_progress_tracking(raw),
            "motivational_message": raw.get("motivational_message", "One day at a time. You've got this!")
        }

        logger.info("Successfully completed quit_porn analysis")
        return normalized

    except GeminiError as e:
        logger.error(f"Gemini AI error in quit_porn analysis: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in quit_porn analysis: {str(e)}", exc_info=True)
        return None

