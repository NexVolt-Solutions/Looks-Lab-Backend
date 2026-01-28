"""
File upload validation utilities.
"""
import os
from pathlib import Path
from fastapi import HTTPException, status

ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}
ALLOWED_FILE_EXTENSIONS = ALLOWED_IMAGE_EXTENSIONS

MAX_FILE_SIZE = 10 * 1024 * 1024


def validate_file_path(file_path: str, max_size: int | None = None) -> None:
    if not file_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File path is required"
        )

    path = Path(file_path)
    extension = path.suffix.lower()

    if extension not in ALLOWED_FILE_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed extensions: {', '.join(ALLOWED_FILE_EXTENSIONS)}"
        )

    if os.path.exists(file_path):
        file_size = os.path.getsize(file_path)
        max_allowed = max_size or MAX_FILE_SIZE

        if file_size > max_allowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File size exceeds maximum allowed size of {max_allowed / (1024 * 1024):.1f}MB"
            )

        if file_size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File is empty"
            )


def validate_file_extension(file_path: str) -> None:
    if not file_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File path is required"
        )

    path = Path(file_path)
    extension = path.suffix.lower()

    if extension not in ALLOWED_FILE_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed extensions: {', '.join(ALLOWED_FILE_EXTENSIONS)}"
        )

