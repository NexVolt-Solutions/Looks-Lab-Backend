from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from app.core.config import settings
from app.core.logging import logger

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
MIME_TO_EXTENSION = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}

MIN_FILE_SIZE_BYTES = 1024
MAX_FILE_SIZE_MB = 10


def _detect_mime_from_bytes(content: bytes) -> str | None:
    if content[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if content[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if content[:4] == b"RIFF" and content[8:12] == b"WEBP":
        return "image/webp"
    return None


def get_extension_for_mime(mime_type: str) -> str:
    return MIME_TO_EXTENSION.get(mime_type, ".jpg")


def normalize_filename_for_mime(filename: str | None, mime_type: str) -> str:
    base_name = Path(filename or "upload").stem or "upload"
    return f"{base_name}{get_extension_for_mime(mime_type)}"


async def validate_upload_file(file: UploadFile) -> str:
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required",
        )

    declared_extension = Path(file.filename).suffix.lower()
    if declared_extension and declared_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"File type '{declared_extension}' not allowed. "
                f"Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
            ),
        )

    content = await file.read()
    await file.seek(0)

    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File is empty",
        )

    if len(content) < MIN_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"File is too small ({len(content)} bytes). Minimum size is {MIN_FILE_SIZE_BYTES} bytes. "
                "Please upload a real photo."
            ),
        )

    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=(
                f"File size {len(content) / (1024 * 1024):.1f}MB exceeds maximum "
                f"{settings.MAX_FILE_SIZE_MB}MB"
            ),
        )

    real_mime = _detect_mime_from_bytes(content)
    if real_mime is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File does not appear to be a valid image. Please upload a real JPEG, PNG, or WebP photo.",
        )

    if file.content_type and file.content_type != real_mime:
        logger.info(
            "Upload MIME mismatch accepted | filename=%s declared=%s detected=%s",
            file.filename,
            file.content_type,
            real_mime,
        )

    if declared_extension and declared_extension != get_extension_for_mime(real_mime):
        logger.info(
            "Upload extension mismatch accepted | filename=%s declared_ext=%s detected=%s",
            file.filename,
            declared_extension,
            real_mime,
        )

    return real_mime
