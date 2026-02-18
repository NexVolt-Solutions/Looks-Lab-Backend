"""
Subscription utility functions.
Helper functions for subscription calculations and business logic.
"""
from datetime import datetime, timedelta
from app.schemas.subscription import PlanType


def calculate_end_date(start_date: datetime, plan: PlanType) -> datetime:
    """
    Calculate subscription end date based on plan type.

    Args:
        start_date: Subscription start datetime
        plan: Plan type (weekly, monthly, yearly)

    Returns:
        Calculated end datetime
    """
    duration_mapping = {
        PlanType.weekly: timedelta(days=7),
        PlanType.monthly: timedelta(days=30),
        PlanType.yearly: timedelta(days=365),
    }

    return start_date + duration_mapping[plan]


def get_plan_price(plan: PlanType) -> float:
    """
    Get price for a given plan type.

    Args:
        plan: Plan type

    Returns:
        Price in USD

    Note:
        In production, this should fetch from database or config
    """
    price_mapping = {
        PlanType.weekly: 4.99,
        PlanType.monthly: 9.99,
        PlanType.yearly: 29.99,
    }

    return price_mapping[plan]


def get_plan_duration_days(plan: PlanType) -> int:
    """
    Get duration in days for a plan type.

    Args:
        plan: Plan type

    Returns:
        Number of days
    """
    duration_mapping = {
        PlanType.weekly: 7,
        PlanType.monthly: 30,
        PlanType.yearly: 365,
    }

    return duration_mapping[plan]


def calculate_savings_percent(plan: PlanType) -> int | None:
    """
    Calculate savings percentage compared to weekly plan.

    Args:
        plan: Plan type

    Returns:
        Savings percentage or None for weekly plan
    """
    if plan == PlanType.weekly:
        return None

    weekly_price = get_plan_price(PlanType.weekly)
    plan_price = get_plan_price(plan)
    plan_days = get_plan_duration_days(plan)

    # Calculate equivalent weekly cost
    weekly_equivalent = (weekly_price / 7) * plan_days

    # Calculate savings
    savings = ((weekly_equivalent - plan_price) / weekly_equivalent) * 100

    return int(round(savings))


def get_plan_features(plan: PlanType) -> list[str]:
    """
    Get feature list for a plan type.

    Args:
        plan: Plan type

    Returns:
        List of features

    Note:
        In production, this should come from database/config
    """
    base_features = [
        "AI-Powered Analysis",
        "Expert Transformations",
        "Priority Post",
        "Unlimited Consultations"
    ]

    if plan == PlanType.monthly:
        return base_features + ["Weekly Progress Reports"]

    if plan == PlanType.yearly:
        return base_features + [
            "Weekly Progress Reports",
            "Best Value - Save 75%",
            "Priority Support"
        ]

    return base_features


def is_plan_upgrade(current_plan: PlanType, new_plan: PlanType) -> bool:
    """
    Check if changing plans is an upgrade.

    Args:
        current_plan: Current plan type
        new_plan: New plan type

    Returns:
        True if upgrade, False if downgrade or same
    """
    plan_hierarchy = {
        PlanType.weekly: 1,
        PlanType.monthly: 2,
        PlanType.yearly: 3
    }

    return plan_hierarchy[new_plan] > plan_hierarchy[current_plan]

