from datetime import date, datetime, timedelta, timezone
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.logging import logger
from app.models.workout_completion import WorkoutCompletion
from app.schemas.workout_completion import (
    WorkoutCompletionOut, WorkoutCompletionSave,
    WeeklyWorkoutSummaryOut, WorkoutProgressSummaryOut, WorkoutSummaryItem
)


class WorkoutCompletionService:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_completion(self, user_id: int, target_date: date, domain: str = "workout") -> Optional[WorkoutCompletionOut]:
        result = await self.db.execute(
            select(WorkoutCompletion).where(
                WorkoutCompletion.user_id == user_id,
                WorkoutCompletion.date == target_date,
                WorkoutCompletion.domain == domain,
            )
        )
        record = result.scalar_one_or_none()
        if not record:
            return None
        return WorkoutCompletionOut(
            date=record.date,
            completed_indices=record.completed_indices or [],
            total_exercises=record.total_exercises,
            score=record.score,
            recovery_completed_indices=record.recovery_completed_indices or [],
        )

    async def save_completion(self, user_id: int, payload: WorkoutCompletionSave, domain: str = "workout") -> WorkoutCompletionOut:
        total = payload.total_exercises or 6
        completed_count = len(payload.completed_indices)
        score = round((completed_count / total) * 100, 1) if total > 0 else 0.0

        result = await self.db.execute(
            select(WorkoutCompletion).where(
                WorkoutCompletion.user_id == user_id,
                WorkoutCompletion.date == payload.date,
                WorkoutCompletion.domain == domain,
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            existing.completed_indices = payload.completed_indices
            existing.total_exercises = total
            existing.score = score
            existing.recovery_completed_indices = payload.recovery_completed_indices or []
        else:
            self.db.add(WorkoutCompletion(
                user_id=user_id,
                domain=domain,
                date=payload.date,
                completed_indices=payload.completed_indices,
                total_exercises=total,
                score=score,
                recovery_completed_indices=payload.recovery_completed_indices or [],
            ))

        await self.db.commit()
        logger.info(f"Workout completion saved for user {user_id} date={payload.date} score={score}")
        return WorkoutCompletionOut(
            date=payload.date,
            completed_indices=payload.completed_indices,
            total_exercises=total,
            score=score,
            recovery_completed_indices=payload.recovery_completed_indices or [],
        )

    async def get_weekly_summary(self, user_id: int) -> WeeklyWorkoutSummaryOut:
        """Returns full ISO week Mon-Sun with 0s for missing days."""
        today = date.today()
        # Get Monday of current ISO week
        monday = today - timedelta(days=today.weekday())
        week_dates = [monday + timedelta(days=i) for i in range(7)]

        result = await self.db.execute(
            select(WorkoutCompletion).where(
                WorkoutCompletion.user_id == user_id,
                WorkoutCompletion.date >= monday,
                WorkoutCompletion.date <= monday + timedelta(days=6),
            )
        )
        records = {r.date: r for r in result.scalars().all()}

        days = []
        for d in week_dates:
            if d in records:
                r = records[d]
                days.append(WorkoutSummaryItem(
                    date=d,
                    score=r.score,
                    completed=len(r.completed_indices or []),
                    total=r.total_exercises,
                ))
            else:
                days.append(WorkoutSummaryItem(date=d, score=0.0, completed=0, total=6))

        scores = [d.score for d in days if d.score > 0]
        week_average = round(sum(scores) / len(scores), 1) if scores else 0.0

        return WeeklyWorkoutSummaryOut(
            user_id=user_id,
            week_average=week_average,
            days=days,
        )

    async def get_progress_summary(self, user_id: int, period: str) -> WorkoutProgressSummaryOut:
        """Get workout progress summary for week, month, or year."""
        today = date.today()

        if period == "week":
            period_start = today - timedelta(days=6)
            total_days = 7
        elif period == "month":
            period_start = today.replace(day=1)
            # days from start of month to today
            total_days = (today - period_start).days + 1
        elif period == "year":
            period_start = today.replace(month=1, day=1)
            total_days = (today - period_start).days + 1
        else:
            period_start = today - timedelta(days=6)
            total_days = 7

        result = await self.db.execute(
            select(WorkoutCompletion).where(
                WorkoutCompletion.user_id == user_id,
                WorkoutCompletion.date >= period_start,
                WorkoutCompletion.date <= today,
            ).order_by(WorkoutCompletion.date.asc())
        )
        records = result.scalars().all()

        days = [
            WorkoutSummaryItem(
                date=r.date,
                score=r.score,
                completed=len(r.completed_indices or []),
                total=r.total_exercises,
            )
            for r in records
        ]

        scores = [r.score for r in records if r.score > 0]
        average_score = round(sum(scores) / len(scores), 1) if scores else 0.0
        total_days_active = len([r for r in records if len(r.completed_indices or []) > 0])
        consistency_percent = round((total_days_active / total_days) * 100, 1) if total_days > 0 else 0.0

        return WorkoutProgressSummaryOut(
            user_id=user_id,
            period=period,
            average_score=average_score,
            total_days_active=total_days_active,
            total_days_in_period=total_days,
            consistency_percent=consistency_percent,
            days=days,
        )


class DailyRecoveryService:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_recovery(self, user_id: int, target_date: date):
        from app.models.daily_recovery import DailyRecovery
        from app.schemas.workout_completion import DailyRecoveryOut
        result = await self.db.execute(
            select(DailyRecovery).where(
                DailyRecovery.user_id == user_id,
                DailyRecovery.date == target_date,
            )
        )
        record = result.scalar_one_or_none()
        from app.schemas.workout_completion import RECOVERY_LABELS, RecoveryItem
        if not record:
            items = [RecoveryItem(label=l, done=False) for l in RECOVERY_LABELS]
            return DailyRecoveryOut(date=target_date, sleep=False, water=False, stretched=False, rested=False, items=items)
        bools = [record.sleep, record.water, record.stretched, record.rested]
        items = [RecoveryItem(label=l, done=b) for l, b in zip(RECOVERY_LABELS, bools)]
        return DailyRecoveryOut(
            date=record.date,
            sleep=record.sleep,
            water=record.water,
            stretched=record.stretched,
            rested=record.rested,
            items=items,
        )

    async def save_recovery(self, user_id: int, payload):
        from app.models.daily_recovery import DailyRecovery
        from app.schemas.workout_completion import DailyRecoveryOut
        result = await self.db.execute(
            select(DailyRecovery).where(
                DailyRecovery.user_id == user_id,
                DailyRecovery.date == payload.date,
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            existing.sleep = payload.sleep
            existing.water = payload.water
            existing.stretched = payload.stretched
            existing.rested = payload.rested
        else:
            self.db.add(DailyRecovery(
                user_id=user_id,
                date=payload.date,
                sleep=payload.sleep,
                water=payload.water,
                stretched=payload.stretched,
                rested=payload.rested,
            ))
        await self.db.commit()
        logger.info(f"Recovery checklist saved for user {user_id} date={payload.date}")
        from app.schemas.workout_completion import RECOVERY_LABELS, RecoveryItem
        bools = [payload.sleep, payload.water, payload.stretched, payload.rested]
        items = [RecoveryItem(label=l, done=b) for l, b in zip(RECOVERY_LABELS, bools)]
        return DailyRecoveryOut(
            date=payload.date,
            sleep=payload.sleep,
            water=payload.water,
            stretched=payload.stretched,
            rested=payload.rested,
            items=items,
        )

    async def get_workout_stats(self, user_id: int):
        from app.models.insight import Insight
        from app.schemas.workout_completion import WorkoutStatsOut
        # Weekly calories: sum of completed exercises * 50 cal per exercise
        today = date.today()
        week_start = today - timedelta(days=6)
        result = await self.db.execute(
            select(WorkoutCompletion).where(
                WorkoutCompletion.user_id == user_id,
                WorkoutCompletion.date >= week_start,
                WorkoutCompletion.date <= today,
            )
        )
        records = result.scalars().all()
        total_completed = sum(len(r.completed_indices or []) for r in records)
        weekly_calories = total_completed * 50

        # Consistency
        days_active = len([r for r in records if len(r.completed_indices or []) > 0])
        consistency_percent = round((days_active / 7) * 100, 1)

        # Strength from AI insight intensity
        strength_label = "+12%"  # default moderate
        try:
            insight_result = await self.db.execute(
                select(Insight).where(
                    Insight.user_id == user_id,
                    Insight.category == "workout",
                ).order_by(Insight.created_at.desc()).limit(1)
            )
            insight = insight_result.scalar_one_or_none()
            if insight and insight.content:
                intensity = (
                    insight.content.get("attributes", {}).get("intensity", "") or ""
                ).lower()
                strength_map = {"low": "+5%", "moderate": "+12%", "high": "+20%"}
                strength_label = strength_map.get(intensity, "+12%")
        except Exception as e:
            logger.warning(f"Could not get strength label for user {user_id}: {e}")

        return WorkoutStatsOut(
            weekly_calories=weekly_calories,
            consistency_percent=consistency_percent,
            strength_label=strength_label,
        )
        
        