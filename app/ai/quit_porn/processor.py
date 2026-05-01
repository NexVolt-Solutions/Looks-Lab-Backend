from typing import Any, Optional

from app.ai.gemini_client import GeminiError, run_gemini_json
from app.ai.quit_porn.prompts import build_context, prompt_quit_porn_full
from app.core.logging import logger


def _safe(data: dict, key: str, default: Any = None) -> Any:
    return data.get(key, default) if data else default


def _normalize_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text or default


def _coerce_int(value: Any, default: int) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _default_attributes() -> dict[str, Any]:
    return {
        "frequency": "Occasionally",
        "triggers": ["Stress / anxiety", "Boredom", "Nighttime / before sleep"],
        "urge_timing": ["Evening", "Night"],
        "coping_mechanisms": "Few activities",
        "commitment_level": "Somewhat committed",
    }


def _default_recovery_path() -> dict[str, Any]:
    return {
        "streak": {
            "current_streak": 0,
            "longest_streak": 0,
            "next_goal": 7,
            "streak_message": "Today is day one. Let's make it count!",
        },
        "daily_tasks": [
            {
                "seq": 1,
                "title": "Set Your Daily Intention",
                "description": "Take a minute to remind yourself why staying clean matters today.",
                "duration": "2 min",
                "completed": False,
            },
            {
                "seq": 2,
                "title": "Evening Reflection",
                "description": "Write down a few wins from the day, even if they feel small.",
                "duration": "5 min",
                "completed": False,
            },
            {
                "seq": 3,
                "title": "Productive Alone Time",
                "description": "Choose a healthy activity for the time you are most likely to feel triggered.",
                "duration": "5 min",
                "completed": False,
            },
            {
                "seq": 4,
                "title": "Connect with Someone",
                "description": "Reach out to a friend or family member for a short check-in.",
                "duration": "10 min",
                "completed": False,
            },
        ],
        "exercises": [
            {
                "seq": 1,
                "title": "Power Pushups",
                "description": "Channel your urge into physical strength. Do as many reps as you can.",
                "category": "physical",
                "duration": "2 min",
                "completed": False,
            },
            {
                "seq": 2,
                "title": "Cold Shower Challenge",
                "description": "A short cold shower helps reset your nervous system and lower impulses.",
                "category": "physical",
                "duration": "2 min",
                "completed": False,
            },
            {
                "seq": 3,
                "title": "Box-Breathing",
                "description": "Inhale 4 sec, hold 4 sec, exhale 4 sec, hold 4 sec.",
                "category": "mental",
                "duration": "4 min",
                "completed": False,
            },
            {
                "seq": 4,
                "title": "Mindful Walk",
                "description": "Take a short walk and focus on your breath and surroundings.",
                "category": "physical",
                "duration": "10 min",
                "completed": False,
            },
            {
                "seq": 5,
                "title": "Gratitude Journal",
                "description": "Write 3 things you are grateful for to shift attention positively.",
                "category": "mental",
                "duration": "3 min",
                "completed": False,
            },
            {
                "seq": 6,
                "title": "Urge Surfing",
                "description": "Observe urge sensations without reacting until they naturally pass.",
                "category": "mental",
                "duration": "5 min",
                "completed": False,
            },
            {
                "seq": 7,
                "title": "Plank Challenge",
                "description": "Hold a plank to build mental and physical resilience.",
                "category": "physical",
                "duration": "2 min",
                "completed": False,
            },
            {
                "seq": 8,
                "title": "Calm Mind Meditation",
                "description": "Sit quietly and focus on slow breathing to reduce impulsivity.",
                "category": "mental",
                "duration": "5 min",
                "completed": False,
            },
            {
                "seq": 9,
                "title": "Trigger Analysis",
                "description": "Write one trigger and one replacement action to use next time.",
                "category": "mental",
                "duration": "4 min",
                "completed": False,
            },
            {
                "seq": 10,
                "title": "Future Self Visualization",
                "description": "Close your eyes and picture your stronger future self for one minute.",
                "category": "mental",
                "duration": "1 min",
                "completed": False,
            },
        ],
    }


def _default_progress_tracking() -> dict[str, Any]:
    return {
        "consistency": "42%",
        "recovery_score": "58%",
        "recovery_checklist": [
            "Set your daily intention",
            "Evening reflection",
            "Productive alone time",
            "Connect with someone",
        ],
    }


def normalize_attributes(data: dict) -> dict[str, Any]:
    try:
        attrs = _safe(data, "attributes", {})
        triggers = attrs.get("triggers", [])
        urge_timing = attrs.get("urge_timing", [])
        defaults = _default_attributes()
        normalized_triggers = [
            _normalize_text(item) for item in triggers[:6]
            if _normalize_text(item)
        ] if isinstance(triggers, list) else []
        normalized_timing = [
            _normalize_text(item) for item in urge_timing[:5]
            if _normalize_text(item)
        ] if isinstance(urge_timing, list) else []
        return {
            "frequency": _normalize_text(attrs.get("frequency"), defaults["frequency"]),
            "triggers": normalized_triggers or defaults["triggers"],
            "urge_timing": normalized_timing or defaults["urge_timing"],
            "coping_mechanisms": _normalize_text(attrs.get("coping_mechanisms"), defaults["coping_mechanisms"]),
            "commitment_level": _normalize_text(attrs.get("commitment_level"), defaults["commitment_level"]),
        }
    except Exception as e:
        logger.error(f"Error normalizing quit_porn attributes: {e}")
        return _default_attributes()


def _normalize_streak(recovery: dict) -> dict[str, Any]:
    try:
        streak = recovery.get("streak", {})
        if not isinstance(streak, dict):
            streak = {}
        defaults = _default_recovery_path()["streak"]
        return {
            "current_streak": _coerce_int(streak.get("current_streak"), defaults["current_streak"]),
            "longest_streak": _coerce_int(streak.get("longest_streak"), defaults["longest_streak"]),
            "next_goal": _coerce_int(streak.get("next_goal"), defaults["next_goal"]),
            "streak_message": _normalize_text(streak.get("streak_message"), defaults["streak_message"]),
        }
    except Exception as e:
        logger.error(f"Error normalizing quit_porn streak: {e}")
        return _default_recovery_path()["streak"]


def _normalize_daily_tasks(recovery: dict) -> list[dict[str, Any]]:
    try:
        tasks_raw = recovery.get("daily_tasks", [])
        if not isinstance(tasks_raw, list):
            return _default_recovery_path()["daily_tasks"]
        tasks = []
        for item in tasks_raw[:5]:
            if isinstance(item, dict):
                tasks.append({
                    "seq": _coerce_int(item.get("seq") or item.get("order"), len(tasks) + 1),
                    "title": _normalize_text(item.get("title")),
                    "description": _normalize_text(item.get("description")),
                    "duration": _normalize_text(item.get("duration"), "5 min"),
                    "completed": bool(item.get("completed", False)),
                })
            elif isinstance(item, str) and item.strip():
                tasks.append({
                    "seq": len(tasks) + 1,
                    "title": item.strip(),
                    "description": "",
                    "duration": "5 min",
                    "completed": False,
                })
        return tasks or _default_recovery_path()["daily_tasks"]
    except Exception as e:
        logger.error(f"Error normalizing quit_porn daily tasks: {e}")
        return _default_recovery_path()["daily_tasks"]


def _normalize_exercises(recovery: dict) -> list[dict[str, Any]]:
    try:
        exercises_raw = recovery.get("exercises", [])
        if not isinstance(exercises_raw, list):
            return []
        exercises = []
        for item in exercises_raw[:10]:
            if isinstance(item, dict):
                exercises.append({
                    "seq": _coerce_int(item.get("seq"), len(exercises) + 1),
                    "title": _normalize_text(item.get("title")),
                    "description": _normalize_text(item.get("description")),
                    "category": _normalize_text(item.get("category"), "mental"),
                    "duration": _normalize_text(item.get("duration"), "5 min"),
                    "completed": bool(item.get("completed", False)),
                })
            elif isinstance(item, str) and item.strip():
                exercises.append({
                    "seq": len(exercises) + 1,
                    "title": item.strip(),
                    "description": "",
                    "category": "mental",
                    "duration": "5 min",
                    "completed": False,
                })
        return exercises or _default_recovery_path()["exercises"]
    except Exception as e:
        logger.error(f"Error normalizing quit_porn exercises: {e}")
        return []


def normalize_recovery_path(data: dict) -> dict[str, Any]:
    try:
        recovery = _safe(data, "recovery_path", {})
        return {
            "streak": _normalize_streak(recovery),
            "daily_tasks": _normalize_daily_tasks(recovery),
            "exercises": _normalize_exercises(recovery),
        }
    except Exception as e:
        logger.error(f"Error normalizing quit_porn recovery path: {e}")
        return _default_recovery_path()


def normalize_progress_tracking(data: dict) -> dict[str, Any]:
    try:
        progress = _safe(data, "progress_tracking", {})
        checklist = progress.get("recovery_checklist", [])
        normalized_checklist = [
            _normalize_text(item) for item in checklist[:4]
            if _normalize_text(item)
        ] if isinstance(checklist, list) else []
        defaults = _default_progress_tracking()
        return {
            "consistency": _normalize_text(progress.get("consistency"), defaults["consistency"]),
            "recovery_score": _normalize_text(progress.get("recovery_score"), defaults["recovery_score"]),
            "recovery_checklist": normalized_checklist or defaults["recovery_checklist"],
        }
    except Exception as e:
        logger.error(f"Error normalizing quit_porn progress tracking: {e}")
        return _default_progress_tracking()


def analyze_quit_porn(answers: list[dict], images: list[dict]) -> Optional[dict[str, Any]]:
    try:
        context = build_context(answers, images)
        raw = run_gemini_json(prompt_quit_porn_full(context), domain="quit porn")

        if not raw:
            logger.warning("Empty response from Gemini for quit_porn analysis")
            return None

        return {
            "attributes": normalize_attributes(raw),
            "recovery_path": normalize_recovery_path(raw),
            "progress_tracking": normalize_progress_tracking(raw),
            "motivational_message": _normalize_text(
                raw.get("motivational_message"),
                "One day at a time. That is all you need to focus on. Keep going!",
            ),
        }
    except GeminiError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in quit_porn analysis: {e}", exc_info=True)
        return None
