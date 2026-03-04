from typing import Any, Optional

from app.ai.gemini_client import GeminiError, run_gemini_json
from app.ai.quit_porn.prompts import build_context, prompt_quit_porn_full
from app.core.logging import logger


def _safe(data: dict, key: str, default: Any = None) -> Any:
    return data.get(key, default) if data else default


def normalize_attributes(data: dict) -> dict[str, Any]:
    try:
        attrs = _safe(data, "attributes", {})
        triggers    = attrs.get("triggers", [])
        urge_timing = attrs.get("urge_timing", [])
        return {
            "frequency":          attrs.get("frequency", "Occasionally"),
            "triggers":           triggers[:6] if isinstance(triggers, list) else [],
            "urge_timing":        urge_timing[:5] if isinstance(urge_timing, list) else [],
            "coping_mechanisms":  attrs.get("coping_mechanisms", "Few activities"),
            "commitment_level":   attrs.get("commitment_level", "Somewhat committed"),
        }
    except Exception as e:
        logger.error(f"Error normalizing quit_porn attributes: {e}")
        return {
            "frequency": "Occasionally", "triggers": [], "urge_timing": [],
            "coping_mechanisms": "Few activities", "commitment_level": "Somewhat committed",
        }


def _normalize_streak(recovery: dict) -> dict[str, Any]:
    try:
        streak = recovery.get("streak", {})
        if not isinstance(streak, dict):
            streak = {}
        return {
            "current_streak": streak.get("current_streak", 0),
            "longest_streak": streak.get("longest_streak", 0),
            "next_goal":      streak.get("next_goal", 7),
            "streak_message": streak.get("streak_message", "Today is day one. Let's make it count!"),
        }
    except Exception as e:
        logger.error(f"Error normalizing quit_porn streak: {e}")
        return {"current_streak": 0, "longest_streak": 0, "next_goal": 7, "streak_message": "Today is day one. Let's make it count!"}


def _normalize_daily_tasks(recovery: dict) -> list[dict[str, Any]]:
    try:
        tasks_raw = recovery.get("daily_tasks", [])
        if not isinstance(tasks_raw, list):
            return []
        tasks = []
        for item in tasks_raw[:5]:
            if isinstance(item, dict):
                tasks.append({
                    "seq":         item.get("seq", len(tasks) + 1),
                    "title":       item.get("title", ""),
                    "description": item.get("description", ""),
                    "duration":    item.get("duration", ""),
                    "completed":   item.get("completed", False),
                })
            elif isinstance(item, str):
                parts = item.split(" — ")
                tasks.append({
                    "seq": len(tasks) + 1,
                    "title": parts[0].strip(),
                    "description": "",
                    "duration": parts[1].strip() if len(parts) > 1 else "",
                    "completed": False,
                })
        return tasks
    except Exception as e:
        logger.error(f"Error normalizing quit_porn daily tasks: {e}")
        return []


def _normalize_exercises(recovery: dict) -> list[dict[str, Any]]:
    try:
        exercises_raw = recovery.get("exercises", [])
        if not isinstance(exercises_raw, list):
            return []
        exercises = []
        for item in exercises_raw[:10]:
            if isinstance(item, dict):
                exercises.append({
                    "seq":         item.get("seq", len(exercises) + 1),
                    "title":       item.get("title", ""),
                    "description": item.get("description", ""),
                    "category":    item.get("category", "mental"),
                    "completed":   item.get("completed", False),
                })
            elif isinstance(item, str):
                parts = item.split(" — ")
                exercises.append({
                    "seq": len(exercises) + 1,
                    "title": parts[0].strip(),
                    "description": "",
                    "category": "mental",
                    "completed": False,
                })
        return exercises
    except Exception as e:
        logger.error(f"Error normalizing quit_porn exercises: {e}")
        return []


def normalize_recovery_path(data: dict) -> dict[str, Any]:
    try:
        recovery = _safe(data, "recovery_path", {})
        return {
            "streak":      _normalize_streak(recovery),
            "daily_tasks": _normalize_daily_tasks(recovery),
            "exercises":   _normalize_exercises(recovery),
        }
    except Exception as e:
        logger.error(f"Error normalizing quit_porn recovery path: {e}")
        return {
            "streak": {"current_streak": 0, "longest_streak": 0, "next_goal": 7, "streak_message": "Today is day one. Let's make it count!"},
            "daily_tasks": [],
            "exercises": [],
        }


def normalize_progress_tracking(data: dict) -> dict[str, Any]:
    try:
        progress  = _safe(data, "progress_tracking", {})
        checklist = progress.get("recovery_checklist", [])
        return {
            "consistency":        progress.get("consistency", "0%"),
            "recovery_score":     progress.get("recovery_score", "0%"),
            "recovery_checklist": [str(i) for i in checklist[:4] if i] if isinstance(checklist, list) else [],
        }
    except Exception as e:
        logger.error(f"Error normalizing quit_porn progress tracking: {e}")
        return {"consistency": "0%", "recovery_score": "0%", "recovery_checklist": []}


def analyze_quit_porn(answers: list[dict], images: list[dict]) -> Optional[dict[str, Any]]:
    try:
        context = build_context(answers, images)
        raw = run_gemini_json(prompt_quit_porn_full(context), domain="quit porn")

        if not raw:
            logger.warning("Empty response from Gemini for quit_porn analysis")
            return None

        return {
            "attributes":           normalize_attributes(raw),
            "recovery_path":        normalize_recovery_path(raw),
            "progress_tracking":    normalize_progress_tracking(raw),
            "motivational_message": raw.get("motivational_message", "One day at a time. That's all you need to focus on. Keep going!"),
        }
    except GeminiError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in quit_porn analysis: {e}", exc_info=True)
        return None

