"""
Domain utility functions.
Pure validation and configuration helpers for domain operations.
"""
from fastapi import HTTPException
from fastapi import status as http_status

from app.enums import DomainEnum


# ── Validation ────────────────────────────────────────────────────

def validate_domain(domain: str) -> None:
    """
    Validate domain against allowed domains.

    Args:
        domain: Domain name to validate

    Raises:
        HTTPException: If domain is not in allowed list
    """
    if domain not in DomainEnum.values():
        raise HTTPException(
            status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid domain. Must be one of: {', '.join(DomainEnum.values())}"
        )


# ── AI Configuration ──────────────────────────────────────────────

def get_ai_config_for_domain(domain: str) -> dict:
    """
    Get AI configuration for a specific domain.

    Args:
        domain: Domain name

    Returns:
        Dictionary with MIN_ANSWERS_REQUIRED and REQUIRE_IMAGES

    Note:
        Returns default config if domain-specific config not found
    """
    from app.ai.diet.config import DietAIConfig
    from app.ai.facial.config import FacialAIConfig
    from app.ai.fashion.config import FashionAIConfig
    from app.ai.hair_care.config import HaircareAIConfig
    from app.ai.height.config import HeightAIConfig
    from app.ai.quit_porn.config import QuitPornAIConfig
    from app.ai.skin_care.config import SkincareAIConfig
    from app.ai.workout.config import WorkoutAIConfig

    configs = {
        "skincare": SkincareAIConfig(),
        "haircare": HaircareAIConfig(),
        "facial": FacialAIConfig(),
        "diet": DietAIConfig(),
        "height": HeightAIConfig(),
        "workout": WorkoutAIConfig(),
        "quit porn": QuitPornAIConfig(),
        "fashion": FashionAIConfig(),
    }

    config = configs.get(domain)

    if not config:
        # Default fallback config
        return {
            "MIN_ANSWERS_REQUIRED": 5,
            "REQUIRE_IMAGES": False,
        }

    return {
        "MIN_ANSWERS_REQUIRED": config.MIN_ANSWERS_REQUIRED,
        "REQUIRE_IMAGES": config.REQUIRE_IMAGES,
    }

