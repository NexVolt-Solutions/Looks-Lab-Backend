"""
Domain utility functions.
Validation helpers and AI configuration only.
Business logic moved to app/services/domain_service.py
"""
from app.enums import DomainEnum
from fastapi import HTTPException, status


# ============================================================
# Validation Helpers (Pure Functions - Can Stay)
# ============================================================

def validate_domain(domain: str) -> None:
    """
    Validate domain against allowed domains.

    Args:
        domain: Domain name to validate

    Raises:
        HTTPException: If domain invalid
    """
    if domain not in DomainEnum.values():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid domain. Must be one of: {', '.join(DomainEnum.values())}"
        )


def get_ai_config_for_domain(domain: str) -> dict:
    """
    Get AI configuration for a specific domain.

    Args:
        domain: Domain name

    Returns:
        Dictionary with MIN_ANSWERS_REQUIRED and REQUIRE_IMAGES
    """
    from app.ai.skin_care.config import SkincareAIConfig
    from app.ai.hair_care.config import HaircareAIConfig
    from app.ai.facial.config import FacialAIConfig
    from app.ai.diet.config import DietAIConfig
    from app.ai.height.config import HeightAIConfig
    from app.ai.workout.config import WorkoutAIConfig
    from app.ai.quit_porn.config import QuitPornAIConfig
    from app.ai.fashion.config import FashionAIConfig

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
        return {"MIN_ANSWERS_REQUIRED": 5, "REQUIRE_IMAGES": False}

    return {
        "MIN_ANSWERS_REQUIRED": config.MIN_ANSWERS_REQUIRED,
        "REQUIRE_IMAGES": config.REQUIRE_IMAGES,
    }

# ============================================================
# DEPRECATED FUNCTIONS
# ============================================================
# All database operations have been moved to DomainService
#
# Migration guide:
# - Old: from app.utils.domain_utils import save_domain_answer, next_or_complete_domain
# - New: from app.services.domain_service import DomainService
#        service = DomainService(db)
#        question = service.save_answer(domain, payload)
#        flow = service.next_or_complete(user_id, domain)

