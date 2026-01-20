"""
File upload validation utilities.
"""
import os
from pathlib import Path
from typing import Optional
from fastapi import HTTPException, status

# Allowed file extensions
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}
ALLOWED_FILE_EXTENSIONS = ALLOWED_IMAGE_EXTENSIONS  # Can be extended for other file types

# Maximum file size (10MB)
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB in bytes


def validate_file_path(file_path: str, max_size: Optional[int] = None) -> None:
    """
    Validate file path, extension, and optionally size.
    
    Args:
        file_path: Path to the file
        max_size: Maximum file size in bytes (defaults to MAX_FILE_SIZE)
    
    Raises:
        HTTPException: If validation fails
    """
    if not file_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File path is required"
        )
    
    # Check extension
    path = Path(file_path)
    extension = path.suffix.lower()
    
    if extension not in ALLOWED_FILE_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed extensions: {', '.join(ALLOWED_FILE_EXTENSIONS)}"
        )
    
    # Check if file exists and validate size
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
    """Validate only the file extension."""
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
