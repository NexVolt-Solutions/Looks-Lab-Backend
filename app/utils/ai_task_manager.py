"""
DB-backed AI task manager.
Stores running/completed AI jobs in ai_jobs so status is shared across workers
and survives process restarts.
"""
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.ai_job import AIJob


def task_key(user_id: int, domain: str) -> str:
    return f"{user_id}:{domain}"


async def _get_or_create_job(db, user_id: int, domain: str) -> AIJob:
    result = await db.execute(
        select(AIJob).where(AIJob.user_id == user_id, AIJob.domain == domain)
    )
    job = result.scalar_one_or_none()
    if job:
        return job

    job = AIJob(user_id=user_id, domain=domain, status="pending")
    db.add(job)
    await db.flush()
    return job


async def set_processing(user_id: int, domain: str) -> None:
    """Mark a task as started."""
    async with AsyncSessionLocal() as db:
        job = await _get_or_create_job(db, user_id, domain)
        job.status = "processing"
        job.result_payload = None
        job.error_message = None
        job.started_at = datetime.now(timezone.utc)
        job.completed_at = None
        await db.commit()


async def set_completed(user_id: int, domain: str, result: Any) -> None:
    """Store completed AI result."""
    payload = result.model_dump(exclude_none=True) if hasattr(result, "model_dump") else result
    async with AsyncSessionLocal() as db:
        job = await _get_or_create_job(db, user_id, domain)
        job.status = "completed"
        job.result_payload = payload if isinstance(payload, dict) else None
        job.error_message = None
        if not job.started_at:
            job.started_at = datetime.now(timezone.utc)
        job.completed_at = datetime.now(timezone.utc)
        await db.commit()


async def set_failed(user_id: int, domain: str, error: str) -> None:
    """Mark task as failed."""
    async with AsyncSessionLocal() as db:
        job = await _get_or_create_job(db, user_id, domain)
        job.status = "failed"
        job.result_payload = None
        job.error_message = error[:1000]
        if not job.started_at:
            job.started_at = datetime.now(timezone.utc)
        job.completed_at = datetime.now(timezone.utc)
        await db.commit()


async def get_task(user_id: int, domain: str) -> Optional[dict[str, Any]]:
    """Get current task state. Returns None if no task exists."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(AIJob).where(AIJob.user_id == user_id, AIJob.domain == domain)
        )
        job = result.scalar_one_or_none()
        if not job:
            return None

        started_at_ts = (
            job.started_at.timestamp()
            if job.started_at
            else 0.0
        )
        return {
            "status": job.status,
            "result": job.result_payload,
            "error": job.error_message,
            "started_at": started_at_ts,
            "submission_hash": job.submission_hash,
        }


async def is_processing(user_id: int, domain: str) -> bool:
    task = await get_task(user_id, domain)
    return task is not None and task["status"] == "processing"


async def is_timed_out(user_id: int, domain: str, timeout_seconds: int = 90) -> bool:
    """Check if a processing task has exceeded the timeout — detects hung Gemini calls."""
    task = await get_task(user_id, domain)
    if not task or task["status"] != "processing":
        return False
    started_at = task.get("started_at", 0)
    return (datetime.now(timezone.utc).timestamp() - started_at) > timeout_seconds


async def clear_task(user_id: int, domain: str) -> None:
    """Clear task state and idempotency hash for user-domain."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(AIJob).where(AIJob.user_id == user_id, AIJob.domain == domain)
        )
        job = result.scalar_one_or_none()
        if job:
            await db.delete(job)
            await db.commit()


async def set_submission_hash(user_id: int, domain: str, hash_value: str) -> None:
    """Store the hash of the last bulk answer submission."""
    async with AsyncSessionLocal() as db:
        job = await _get_or_create_job(db, user_id, domain)
        job.submission_hash = hash_value
        await db.commit()


async def get_submission_hash(user_id: int, domain: str) -> Optional[str]:
    """Get the hash of the last bulk answer submission."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(AIJob.submission_hash).where(AIJob.user_id == user_id, AIJob.domain == domain)
        )
        row = result.first()
        return row[0] if row else None

