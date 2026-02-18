"""
File upload validation utilities.
"""
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from app.core.config import settings
from app.core.logging import logger


# ── Constants ─────────────────────────────────────────────────────

ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

ALLOWED_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
}


# ── Validators ────────────────────────────────────────────────────

async def validate_upload_file(file: UploadFile) -> None:
    """
    Validate FastAPI UploadFile object.
    Used directly in image upload routes.

    Checks:
    - Filename present
    - Extension allowed
    - MIME type allowed
    - File not empty
    - File size within limit
    """
    # 1. Filename check
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required"
        )

    # 2. Extension check
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"File type '{ext}' not allowed. "
                f"Allowed: {', '.join(sorted(ALLOWED_IMAGE_EXTENSIONS))}"
            )
        )

    # 3. MIME type check
    if file.content_type and file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Content type '{file.content_type}' not allowed. "
                f"Allowed: {', '.join(sorted(ALLOWED_MIME_TYPES))}"
            )
        )

    # 4. Read and check content
    content = await file.read()

    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File is empty"
        )

    # 5. Size check
    max_size = settings.max_file_size_bytes
    if len(content) > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=(
                f"File size {len(content) / (1024 * 1024):.1f}MB "
                f"exceeds maximum allowed {settings.MAX_FILE_SIZE_MB}MB"
            )
        )


    await file.seek(0)

    logger.debug(
        f"File validated: {file.filename} "
        f"({len(content) / 1024:.1f}KB, {file.content_type})"
    )


def validate_file_path(file_path: str, max_size: int | None = None) -> None:
    """
    Validate a file that already exists on disk.
    Used for local storage validation.

    Checks:
    - Path provided
    - Extension allowed
    - File exists and not empty
    - File size within limit
    """
    if not file_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File path is required"
        )

    path = Path(file_path)
    ext = path.suffix.lower()

    # Extension check
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"File type '{ext}' not allowed. "
                f"Allowed: {', '.join(sorted(ALLOWED_IMAGE_EXTENSIONS))}"
            )
        )


    if path.exists():
        file_size = path.stat().st_size

        if file_size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File is empty"
            )

        max_allowed = max_size or settings.max_file_size_bytes
        if file_size > max_allowed:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=(
                    f"File size {file_size / (1024 * 1024):.1f}MB "
                    f"exceeds maximum allowed {settings.MAX_FILE_SIZE_MB}MB"
                )
            )

