from datetime import datetime, timezone, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.models.domain_score_history import DomainScoreHistory
from app.models.insight import Insight
from app.models.workout_completion import WorkoutCompletion
from app.schemas.progress import DomainScorePoint, DomainProgressSeries, ProgressGraphOut
from app.utils.domain_score_utils import extract_domain_score

_DOMAIN_ICONS = {
    "skincare": "https://api.lookslabai.com/static/icons/SkinCare.jpg",
    "haircare": "https://api.lookslabai.com/static/icons/Hair.png",
    "fashion": "https://api.lookslabai.com/static/icons/Fashion.png",
    "workout": "https://api.lookslabai.com/static/icons/Workout.jpg",
    "diet": "https://api.lookslabai.com/static/icons/Diet.jpg",
    "height": "https://api.lookslabai.com/static/icons/Height.jpg",
    "quit_porn": "https://api.lookslabai.com/static/icons/QuitPorn.jpg",
    "facial": "https://api.lookslabai.com/static/icons/Facial.jpg",
}

_PERIOD_DAYS = {
    "weekly": 7,
    "monthly": 30,
    "yearly": 365,
}


class ProgressService:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def save_score_snapshot(self, user_id: int, domain: str, score: float) -> None:
        """
        Called by domain_service after AI runs.
        - First time AI runs for this domain: saves with is_first_score=True (permanent before score)
        - Subsequent runs: saves normally with is_first_score=False (updates after score)
        """
        try:
            result = await self.db.execute(
                select(DomainScoreHistory).where(
                    DomainScoreHistory.user_id == user_id,
                    DomainScoreHistory.domain == domain,
                    DomainScoreHistory.is_first_score == True,  # noqa: E712
                )
            )
            has_first_score = result.scalar_one_or_none() is not None

            snapshot = DomainScoreHistory(
                user_id=user_id,
                domain=domain,
                score=score,
                is_first_score=not has_first_score,
                recorded_at=datetime.now(timezone.utc),
            )
            self.db.add(snapshot)
            await self.db.commit()
            logger.info(
                f"Saved score snapshot for user {user_id} domain {domain}: "
                f"{score} (first={not has_first_score})"
            )
        except Exception as e:
            logger.error(f"Failed to save score snapshot: {e}")

    async def _get_latest_scored_insights(self, user_id: int) -> dict[str, Insight]:
        result = await self.db.execute(
            select(Insight)
            .where(Insight.user_id == user_id)
            .order_by(Insight.category.asc(), Insight.updated_at.desc(), Insight.created_at.desc())
        )

        latest_by_domain: dict[str, Insight] = {}
        for insight in result.scalars().all():
            domain = insight.category.value if hasattr(insight.category, "value") else str(insight.category)
            if domain in latest_by_domain:
                continue

            score = insight.score
            if score is None and isinstance(insight.content, dict):
                score = extract_domain_score(domain, insight.content)
            if score is None:
                continue

            latest_by_domain[domain] = insight

        return latest_by_domain

    async def get_progress_graph(self, user_id: int, period: str) -> ProgressGraphOut:
        days = _PERIOD_DAYS.get(period, 7)
        since = datetime.now(timezone.utc) - timedelta(days=days)

        result = await self.db.execute(
            select(DomainScoreHistory)
            .where(DomainScoreHistory.user_id == user_id)
            .order_by(DomainScoreHistory.domain, DomainScoreHistory.recorded_at.asc())
        )
        all_records = result.scalars().all()
        latest_insights = await self._get_latest_scored_insights(user_id)

        grouped_all: dict[str, list[DomainScoreHistory]] = {}
        grouped_period: dict[str, list[DomainScoreHistory]] = {}
        for record in all_records:
            grouped_all.setdefault(record.domain, []).append(record)
            if record.recorded_at >= since:
                grouped_period.setdefault(record.domain, []).append(record)

        domain_series = []
        all_first_scores = []
        all_latest_scores = []

        all_domains = set(grouped_all.keys()) | set(latest_insights.keys()) | set(_DOMAIN_ICONS.keys())

        for domain in sorted(all_domains):
            lifetime_records = grouped_all.get(domain, [])
            period_records = grouped_period.get(domain, [])
            score_points = [
                DomainScorePoint(
                    domain=r.domain,
                    score=round(r.score, 1),
                    recorded_at=r.recorded_at,
                )
                for r in period_records
            ]

            first_score = 0.0
            latest_score = 0.0
            has_score_data = False

            if lifetime_records:
                first_score = round(lifetime_records[0].score, 1)
                latest_score = round(lifetime_records[-1].score, 1)
                has_score_data = True
            else:
                fallback_insight = latest_insights.get(domain)
                if fallback_insight is not None:
                    fallback_score = fallback_insight.score
                    if fallback_score is None and isinstance(fallback_insight.content, dict):
                        fallback_score = extract_domain_score(domain, fallback_insight.content)

                    if fallback_score is not None:
                        first_score = round(fallback_score, 1)
                        latest_score = round(fallback_score, 1)
                        has_score_data = True

                        if fallback_insight.updated_at >= since:
                            score_points = [
                                DomainScorePoint(
                                    domain=domain,
                                    score=round(fallback_score, 1),
                                    recorded_at=fallback_insight.updated_at,
                                )
                            ]

            change = round(latest_score - first_score, 1)

            if has_score_data:
                all_first_scores.append(first_score)
                all_latest_scores.append(latest_score)

            domain_series.append(
                DomainProgressSeries(
                    domain=domain,
                    icon_url=_DOMAIN_ICONS.get(domain),
                    scores=score_points,
                    first_score=first_score,
                    latest_score=latest_score,
                    change=change,
                )
            )

        overall_first = round(sum(all_first_scores) / len(all_first_scores), 1) if all_first_scores else 0.0
        overall_latest = round(sum(all_latest_scores) / len(all_latest_scores), 1) if all_latest_scores else 0.0
        overall_change = round(overall_latest - overall_first, 1)

        return ProgressGraphOut(
            period=period,
            domains=domain_series,
            overall_first=overall_first,
            overall_latest=overall_latest,
            overall_change=overall_change,
        )

    async def _get_completion_backed_domain_progress_graph(self, user_id: int, domain: str, period: str) -> dict:
        days = _PERIOD_DAYS.get(period, 7)
        since_date = (datetime.now(timezone.utc) - timedelta(days=days)).date()

        result = await self.db.execute(
            select(WorkoutCompletion)
            .where(
                WorkoutCompletion.user_id == user_id,
                WorkoutCompletion.domain == domain,
                WorkoutCompletion.date >= since_date,
            )
            .order_by(WorkoutCompletion.date.asc(), WorkoutCompletion.recorded_at.asc())
        )
        records = result.scalars().all()

        scores = [
            {
                "domain": domain,
                "score": round(record.score, 1),
                "recorded_at": record.recorded_at,
            }
            for record in records
        ]

        first_score = round(records[0].score, 1) if records else 0.0
        latest_score = round(records[-1].score, 1) if records else 0.0
        change = round(latest_score - first_score, 1) if records else 0.0

        return {
            "period": period,
            "domain": domain,
            "icon_url": _DOMAIN_ICONS.get(domain),
            "first_score": first_score,
            "latest_score": latest_score,
            "change": change,
            "scores": scores,
        }

    async def get_domain_progress_graph(self, user_id: int, domain: str, period: str) -> dict:
        if domain == "quit_porn":
            return await self._get_completion_backed_domain_progress_graph(user_id, domain, period)

        graph = await self.get_progress_graph(user_id, period)
        domain_data = next((d for d in graph.domains if d.domain == domain), None)
        if not domain_data:
            return {
                "period": period,
                "domain": domain,
                "icon_url": _DOMAIN_ICONS.get(domain),
                "first_score": 0.0,
                "latest_score": 0.0,
                "change": 0.0,
                "scores": [],
            }
        return {
            "period": period,
            "domain": domain_data.domain,
            "icon_url": domain_data.icon_url,
            "first_score": domain_data.first_score,
            "latest_score": domain_data.latest_score,
            "change": domain_data.change,
            "scores": [
                {"domain": s.domain, "score": s.score, "recorded_at": s.recorded_at}
                for s in domain_data.scores
            ],
        }
