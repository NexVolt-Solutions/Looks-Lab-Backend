from datetime import datetime, timezone, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.models.domain_score_history import DomainScoreHistory
from app.schemas.progress import DomainScorePoint, DomainProgressSeries, ProgressGraphOut

_DOMAIN_ICONS = {
    "skincare":  "https://api.lookslabai.com/static/icons/SkinCare.jpg",
    "haircare":  "https://api.lookslabai.com/static/icons/Hair.png",
    "fashion":   "https://api.lookslabai.com/static/icons/Fashion.png",
    "workout":   "https://api.lookslabai.com/static/icons/Workout.jpg",
    "diet":      "https://api.lookslabai.com/static/icons/Diet.jpg",
    "height":    "https://api.lookslabai.com/static/icons/Height.jpg",
    "quit_porn": "https://api.lookslabai.com/static/icons/QuitPorn.jpg",
    "facial":    "https://api.lookslabai.com/static/icons/Facial.jpg",
}

_PERIOD_DAYS = {
    "weekly":  7,
    "monthly": 30,
    "yearly":  365,
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
            # Check if a first score already exists for this user+domain
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
                is_first_score=not has_first_score,  # True only on first ever AI run
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

    async def get_progress_graph(self, user_id: int, period: str) -> ProgressGraphOut:
        days = _PERIOD_DAYS.get(period, 7)
        since = datetime.now(timezone.utc) - timedelta(days=days)

        # Fetch all scores in the requested period
        result = await self.db.execute(
            select(DomainScoreHistory)
            .where(
                DomainScoreHistory.user_id == user_id,
                DomainScoreHistory.recorded_at >= since,
            )
            .order_by(DomainScoreHistory.domain, DomainScoreHistory.recorded_at.asc())
        )
        period_records = result.scalars().all()

        # Fetch all first scores (before progress — static, never changes)
        result = await self.db.execute(
            select(DomainScoreHistory)
            .where(
                DomainScoreHistory.user_id == user_id,
                DomainScoreHistory.is_first_score == True,  # noqa: E712
            )
        )
        first_scores = {r.domain: r.score for r in result.scalars().all()}

        # Group period records by domain
        grouped: dict[str, list[DomainScoreHistory]] = {}
        for record in period_records:
            grouped.setdefault(record.domain, []).append(record)

        domain_series = []
        all_first_scores = []
        all_latest_scores = []

        # Always include all known domains, even if no scores in period
        all_domains = set(grouped.keys()) | set(first_scores.keys()) | set(_DOMAIN_ICONS.keys())

        for domain in sorted(all_domains):
            records = grouped.get(domain, [])
            score_points = [
                DomainScorePoint(
                    domain=r.domain,
                    score=round(r.score, 1),
                    recorded_at=r.recorded_at,
                )
                for r in records
            ]

            # Before = permanent first score ever recorded (static)
            first_score = round(first_scores.get(domain, 0.0), 1)
            # After = latest score in period, or fall back to first_score
            latest_score = round(records[-1].score, 1) if records else first_score
            change = round(latest_score - first_score, 1)

            all_first_scores.append(first_score)
            all_latest_scores.append(latest_score)

            domain_series.append(DomainProgressSeries(
                domain=domain,
                icon_url=_DOMAIN_ICONS.get(domain),
                scores=score_points,
                first_score=first_score,
                latest_score=latest_score,
                change=change,
            ))

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
    async def get_domain_progress_graph(self, user_id: int, domain: str, period: str) -> dict:
        """Get progress graph for a single domain."""
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
        
        