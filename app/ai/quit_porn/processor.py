"""
Quit porn domain AI processor.
Generates structured recovery plans for behavioral wellness.
"""
from typing import Any

from app.ai.gemini_client import run_gemini_json, GeminiError
from app.ai.quit_porn.prompts import prompt_quit_porn_full, build_context
from app.core.logging import logger


def _get_safe_value(data: dict, key: str, default: Any = None) -> Any:
    return data.get(key, default) if data else default


def normalize_attributes(data: dict) -> dict[str, Any]:
    """
    Matches Figma questionnaire screens:
    Frequency, Triggers, Urge Timing, Coping, Commitment
    """
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
            "triggers": triggers[:6],
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


def normalize_streak(data: dict) -> dict[str, Any]:
    """
    Matches Figma Recovery Path screen:
    Current Streak, Longest Streak, Next Goal, Message
    """
    try:
        streak = data.get("streak", {})
        if not isinstance(streak, dict):
            streak = {}

        return {
            "current_streak": streak.get("current_streak", 0),
            "longest_streak": streak.get("longest_streak", 0),
            "next_goal": streak.get("next_goal", 7),
            "streak_message": streak.get(
                "streak_message",
                "Today is day one. Let's make it count!"
            )
        }
    except Exception as e:
        logger.error(f"Error normalizing quit_porn streak: {str(e)}")
        return {
            "current_streak": 0,
            "longest_streak": 0,
            "next_goal": 7,
            "streak_message": "Today is day one. Let's make it count!"
        }


def normalize_daily_tasks(data: dict) -> list[dict[str, Any]]:
    """
    Matches Figma Daily Plan tab:
    Set Daily Intention, Evening Reflection,
    Productive Alone Time, Connect with Someone
    """
    try:
        tasks_raw = data.get("daily_tasks", [])

        if not isinstance(tasks_raw, list):
            return []

        tasks = []
        for item in tasks_raw[:5]:
            if isinstance(item, dict):
                tasks.append({
                    "seq": item.get("seq", len(tasks) + 1),
                    "title": item.get("title", ""),
                    "description": item.get("description", ""),
                    "duration": item.get("duration", ""),
                    "completed": item.get("completed", False)
                })
            elif isinstance(item, str):
                # Fallback for plain string format
                parts = item.split(" — ")
                tasks.append({
                    "seq": len(tasks) + 1,
                    "title": parts[0].strip() if parts else item,
                    "description": "",
                    "duration": parts[1].strip() if len(parts) > 1 else "",
                    "completed": False
                })

        return tasks
    except Exception as e:
        logger.error(f"Error normalizing quit_porn daily tasks: {str(e)}")
        return []


def normalize_exercises(data: dict) -> list[dict[str, Any]]:
    """
    Matches Figma Exercise tab:
    10 Mental & Physical Exercises with category
    (Power Pushups, Cold Shower, Box Breathing, etc.)
    """
    try:
        exercises_raw = data.get("exercises", [])

        if not isinstance(exercises_raw, list):
            return []

        exercises = []
        for item in exercises_raw[:10]:
            if isinstance(item, dict):
                exercises.append({
                    "seq": item.get("seq", len(exercises) + 1),
                    "title": item.get("title", ""),
                    "description": item.get("description", ""),
                    "category": item.get("category", "mental"),  # mental | physical
                    "completed": item.get("completed", False)
                })
            elif isinstance(item, str):
                # Fallback for plain string format
                parts = item.split(" — ")
                exercises.append({
                    "seq": len(exercises) + 1,
                    "title": parts[0].strip() if parts else item,
                    "description": "",
                    "category": "mental",
                    "completed": False
                })

        return exercises
    except Exception as e:
        logger.error(f"Error normalizing quit_porn exercises: {str(e)}")
        return []


def normalize_recovery_path(data: dict) -> dict[str, Any]:
    """
    Matches Figma Recovery Path screen:
    Streak + Daily Tasks + Exercises (combined)
    """
    try:
        recovery = _get_safe_value(data, "recovery_path", {})

        return {
            "streak": normalize_streak(recovery),
            "daily_tasks": normalize_daily_tasks(recovery),
            "exercises": normalize_exercises(recovery),
        }
    except Exception as e:
        logger.error(f"Error normalizing quit_porn recovery path: {str(e)}")
        return {
            "streak": {
                "current_streak": 0,
                "longest_streak": 0,
                "next_goal": 7,
                "streak_message": "Today is day one. Let's make it count!"
            },
            "daily_tasks": [],
            "exercises": []
        }


def normalize_progress_tracking(data: dict) -> dict[str, Any]:
    """
    Matches Figma Your Progress section:
    Consistency, Recovery Score, Recovery Checklist
    """
    try:
        progress = _get_safe_value(data, "progress_tracking", {})

        checklist = progress.get("recovery_checklist", [])
        if not isinstance(checklist, list):
            checklist = []

        return {
            "consistency": progress.get("consistency", "0%"),
            "recovery_score": progress.get("recovery_score", "0%"),
            "recovery_checklist": [
                str(item) for item in checklist[:4] if item
            ]
        }
    except Exception as e:
        logger.error(f"Error normalizing quit_porn progress tracking: {str(e)}")
        return {
            "consistency": "0%",
            "recovery_score": "0%",
            "recovery_checklist": []
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
            "motivational_message": raw.get(
                "motivational_message",
                "One day at a time. That's all you need to focus on. Keep going!"
            )
        }

        logger.info("Successfully completed quit_porn analysis")
        return normalized

    except GeminiError as e:
        logger.error(f"Gemini AI error in quit_porn analysis: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in quit_porn analysis: {str(e)}", exc_info=True)
        return None

