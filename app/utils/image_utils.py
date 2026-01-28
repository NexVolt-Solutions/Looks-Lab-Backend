"""
Image utility functions.
Pure validation and helper functions only.
Database operations moved to app/services/image_service.py
"""
from app.models.image import ImageStatus, ImageType
from fastapi import HTTPException, status


# ============================================================
# Validation Helpers (Pure Functions - Can Stay)
# ============================================================

def validate_image_type(image_type: ImageType) -> None:
    """
    Validate image type enum.

    Args:
        image_type: ImageType enum value

    Raises:
        HTTPException: If invalid
    """
    if image_type not in ImageType.__members__.values():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid image type. Must be one of: {', '.join([t.value for t in ImageType])}"
        )


def validate_image_status(image_status: ImageStatus) -> None:
    """
    Validate image status enum.

    Args:
        image_status: ImageStatus enum value

    Raises:
        HTTPException: If invalid
    """
    if image_status not in ImageStatus.__members__.values():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid image status. Must be one of: {', '.join([s.value for s in ImageStatus])}"
        )

# ============================================================
# DEPRECATED FUNCTIONS
# ============================================================
# All database operations have been moved to ImageService
#
# Migration guide:
# - Old: from app.utils.image_utils import create_image_entry, get_image_status
# - New: from app.services.image_service import ImageService
#        service = ImageService(db)
#        image = await service.upload_image(file, user_id, domain, view)
#        image = service.get_image(image_id, user_id)

