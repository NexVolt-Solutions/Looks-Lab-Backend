"""
Onboarding utility functions.
Constants and validation helpers for onboarding flow.
"""
from app.enums import DomainEnum


# ── Constants ─────────────────────────────────────────────────────

ONBOARDING_ORDER = [
    "profile_setup",
    "daily_lifestyle",
    "motivation",
    "goals_focus",
    "experience_planning",
]


# ── Validation ────────────────────────────────────────────────────

def validate_domain(domain: str) -> None:
    """
    Validate domain name against allowed domains.

    Args:
        domain: Domain name to validate

    Raises:
        ValueError: If domain is not in allowed list
    """
    valid_domains = DomainEnum.values()
    if domain not in valid_domains:
        raise ValueError(
            f"Invalid domain. Must be one of: {', '.join(valid_domains)}"
        )


def get_next_step(current_step: str) -> str | None:
    """
    Get the next step in onboarding order.

    Args:
        current_step: Current step name

    Returns:
        Next step name or None if onboarding is complete
    """
    try:
        idx = ONBOARDING_ORDER.index(current_step)
        return (
            ONBOARDING_ORDER[idx + 1]
            if idx + 1 < len(ONBOARDING_ORDER)
            else None
        )
    except ValueError:
        return None

