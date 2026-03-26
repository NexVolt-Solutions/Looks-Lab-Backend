from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.core.rate_limit import RateLimits, limiter
from app.models.user import User
from app.schemas.workout_completion import (
    WorkoutCompletionOut, WorkoutCompletionSave,
    WeeklyWorkoutSummaryOut, WorkoutProgressSummaryOut,
    DailyRecoveryOut, DailyRecoverySave, WorkoutStatsOut
)
from app.services.workout_completion_service import WorkoutCompletionService
from app.utils.jwt_utils import get_current_user

router = APIRouter()


@router.get("/workout/completed-exercises", response_model=WorkoutCompletionOut)
@limiter.limit(RateLimits.DEFAULT)
async def get_completed_exercises(
    request: Request,
    date: date,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    service = WorkoutCompletionService(db)
    result = await service.get_completion(current_user.id, date)
    if not result:
        return WorkoutCompletionOut(
            date=date,
            completed_indices=[],
            total_exercises=6,
            score=0.0,
        )
    return result


@router.put("/workout/completed-exercises", response_model=WorkoutCompletionOut)
@limiter.limit(RateLimits.DEFAULT)
async def save_completed_exercises(
    request: Request,
    payload: WorkoutCompletionSave,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    service = WorkoutCompletionService(db)
    return await service.save_completion(current_user.id, payload)


@router.get("/workout/weekly-summary", response_model=WeeklyWorkoutSummaryOut)
@limiter.limit(RateLimits.DEFAULT)
async def get_weekly_workout_summary(
    request: Request,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    service = WorkoutCompletionService(db)
    return await service.get_weekly_summary(current_user.id)


@router.get("/workout/progress-summary", response_model=WorkoutProgressSummaryOut)
@limiter.limit(RateLimits.DEFAULT)
async def get_workout_progress_summary(
    request: Request,
    period: Literal["week", "month", "year"] = Query(default="week"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get workout progress summary for week, month, or year.

    - period=week  ? last 7 days
    - period=month ? current month from day 1
    - period=year  ? current year from Jan 1
    """
    service = WorkoutCompletionService(db)
    return await service.get_progress_summary(current_user.id, period)


@router.get("/workout/recovery-checklist", response_model=DailyRecoveryOut)
@limiter.limit(RateLimits.DEFAULT)
async def get_recovery_checklist(
    request: Request,
    date: date,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    """Get daily recovery checklist for a specific date."""
    from app.services.workout_completion_service import DailyRecoveryService
    service = DailyRecoveryService(db)
    return await service.get_recovery(current_user.id, date)


@router.put("/workout/recovery-checklist", response_model=DailyRecoveryOut)
@limiter.limit(RateLimits.DEFAULT)
async def save_recovery_checklist(
    request: Request,
    payload: DailyRecoverySave,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    """Save or update daily recovery checklist."""
    from app.services.workout_completion_service import DailyRecoveryService
    service = DailyRecoveryService(db)
    return await service.save_recovery(current_user.id, payload)


@router.get("/workout/stats", response_model=WorkoutStatsOut)
@limiter.limit(RateLimits.DEFAULT)
async def get_workout_stats(
    request: Request,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get workout stats for the progress screen top cards:
    - weekly_calories: estimated calories burned this week
    - consistency_percent: % of days active this week
    - strength_label: strength gain label from AI (e.g. '+12%')
    """
    from app.services.workout_completion_service import DailyRecoveryService
    service = DailyRecoveryService(db)
    return await service.get_workout_stats(current_user.id)
    
    