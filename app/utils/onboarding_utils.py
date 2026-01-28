"""
Onboarding utility functions.
Constants and validation helpers only.
Business logic moved to app/services/onboarding_service.py
"""

# ============================================================
# Constants (Can Stay - Used by Service)
# ============================================================

ONBOARDING_ORDER = [
    "profile_setup",
    "daily_lifestyle",
    "motivation",
    "goals_focus",
    "experience_planning",
]

VALID_DOMAINS = {
    "skincare",
    "haircare",
    "fashion",
    "workout",
    "quit porn",
    "diet",
    "height",
    "facial",
}


# ============================================================
# Validation Helpers (Pure Functions - Can Stay)
# ============================================================

def validate_domain(domain: str) -> None:
    """
    Validate domain name.

    Args:
        domain: Domain name to validate

    Raises:
        ValueError: If domain invalid
    """
    if domain not in VALID_DOMAINS:
        raise ValueError(f"Invalid domain. Must be one of: {', '.join(VALID_DOMAINS)}")


def get_next_step(current_step: str) -> str | None:
    """
    Get the next step in onboarding order.

    Args:
        current_step: Current step name

    Returns:
        Next step name or None if complete
    """
    try:
        idx = ONBOARDING_ORDER.index(current_step)
        return ONBOARDING_ORDER[idx + 1] if idx + 1 < len(ONBOARDING_ORDER) else None
    except ValueError:
        return None

# ============================================================
# DEPRECATED FUNCTIONS
# ============================================================
# All database operations have been moved to OnboardingService
#
# Migration guide:
# - Old: from app.utils.onboarding_utils import create_session, save_answer
# - New: from app.services.onboarding_service import OnboardingService
#        service = OnboardingService(db)
#        session = service.create_session(user_id)
#        question = service.save_answer(session_id, payload)
