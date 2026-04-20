from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from app.core.config import settings

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}

# Real file signatures (magic bytes) for allowed image types
# These cannot be faked by renaming a file
MAGIC_BYTES: dict[bytes, str] = {
    b"\xff\xd8\xff": "image/jpeg",   # JPEG
    b"\x89PNG\r\n\x1a\n": "image/png",  # PNG
    b"RIFF": "image/webp",              # WebP (starts with RIFF....WEBP)
}

# Size limits
MIN_FILE_SIZE_BYTES = 1024        # 1KB minimum — rejects blank/corrupt files
MAX_FILE_SIZE_MB = 10             # 10MB maximum


def _detect_mime_from_bytes(content: bytes) -> str | None:
    """Detect real MIME type from file magic bytes — cannot be spoofed."""
    if content[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if content[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if content[:4] == b"RIFF" and content[8:12] == b"WEBP":
        return "image/webp"
    return None


async def validate_upload_file(file: UploadFile) -> None:
    # 1. Filename required
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required"
        )

    # 2. Extension check
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type '{ext}' not allowed. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )

    # 3. Read file content once
    content = await file.read()
    await file.seek(0)

    # 4. Empty file check
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File is empty"
        )

    # 5. Minimum size check — rejects blank, corrupt, or placeholder images
    if len(content) < MIN_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File is too small ({len(content)} bytes). Minimum size is {MIN_FILE_SIZE_BYTES} bytes. Please upload a real photo."
        )

    # 6. Maximum size check
    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size {len(content) / (1024 * 1024):.1f}MB exceeds maximum {settings.MAX_FILE_SIZE_MB}MB"
        )

    # 7. Magic bytes check — verify actual file type, cannot be spoofed by renaming
    real_mime = _detect_mime_from_bytes(content)
    if real_mime is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File does not appear to be a valid image. Please upload a real JPEG, PNG, or WebP photo."
        )

    # 8. MIME type consistency check — ensure declared type matches real type
    if file.content_type and file.content_type in ALLOWED_MIME_TYPES:
        if file.content_type != real_mime:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File content does not match declared type. Expected {file.content_type} but file appears to be {real_mime}."
            )

