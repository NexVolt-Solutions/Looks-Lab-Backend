"""
In-memory AI task manager.
Tracks running/completed AI jobs so Flutter can poll for results
instead of waiting 15-25 seconds for Gemini to respond.

Key:   f"{user_id}:{domain}"
Value: {"status": "processing"|"completed"|"failed", "result": DomainFlowOut|None, "error": str|None}
"""
import asyncio
from typing import Any, Optional

_tasks: dict[str, dict[str, Any]] = {}


def task_key(user_id: int, domain: str) -> str:
    return f"{user_id}:{domain}"


def set_processing(user_id: int, domain: str) -> None:
    """Mark a task as started."""
    _tasks[task_key(user_id, domain)] = {
        "status": "processing",
        "result": None,
        "error": None,
    }


def set_completed(user_id: int, domain: str, result: Any) -> None:
    """Store completed AI result."""
    _tasks[task_key(user_id, domain)] = {
        "status": "completed",
        "result": result,
        "error": None,
    }


def set_failed(user_id: int, domain: str, error: str) -> None:
    """Mark task as failed."""
    _tasks[task_key(user_id, domain)] = {
        "status": "failed",
        "result": None,
        "error": error,
    }


def get_task(user_id: int, domain: str) -> Optional[dict[str, Any]]:
    """Get current task state. Returns None if no task exists."""
    return _tasks.get(task_key(user_id, domain))


def is_processing(user_id: int, domain: str) -> bool:
    task = get_task(user_id, domain)
    return task is not None and task["status"] == "processing"


def clear_task(user_id: int, domain: str) -> None:
    """Remove task from memory (optional cleanup)."""
    _tasks.pop(task_key(user_id, domain), None)
    
    