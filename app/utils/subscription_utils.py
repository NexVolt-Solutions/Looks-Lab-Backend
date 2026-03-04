from datetime import datetime, timedelta
from app.schemas.subscription import PlanType


def calculate_end_date(start_date: datetime, plan: PlanType) -> datetime:
    duration = {
        PlanType.weekly: timedelta(days=7),
        PlanType.monthly: timedelta(days=30),
        PlanType.yearly: timedelta(days=365),
    }
    return start_date + duration[plan]

