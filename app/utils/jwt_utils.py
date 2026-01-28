"""
JWT authentication utilities.
Handles token creation, validation, and user authentication.
"""
from jose import jwt, JWTError, ExpiredSignatureError
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import uuid4

from app.core.config import settings
from app.core.database import get_async_db
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/google")


# ============================================================
# Token Creation & Validation
# ============================================================

def create_access_token(data: dict) -> str:
    """
    Create a short-lived JWT access token.

    Args:
        data: Payload to encode (typically user_id and email)

    Returns:
        Encoded JWT string
    """
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.JWT_EXPIRATION_MINUTES)
    to_encode.update({"exp": expire, "iat": now})

    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """
    Decode and validate a JWT access token.

    Args:
        token: JWT string

    Returns:
        Decoded payload

    Raises:
        HTTPException: If token expired or invalid
    """
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )


def create_refresh_token() -> str:
    """
    Generate a secure opaque refresh token.

    Returns:
        UUID string
    """
    return str(uuid4())


def get_refresh_expiry() -> datetime:
    """
    Calculate refresh token expiry timestamp.

    Returns:
        UTC datetime for expiration
    """
    return datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRATION_DAYS)


def get_current_time() -> datetime:
    """
    Get current UTC timestamp.

    Returns:
        Current UTC datetime
    """
    return datetime.now(timezone.utc)


# ============================================================
# User Helpers
# ============================================================

def ensure_user_active(user: User) -> None:
    """
    Ensure user account is active.

    Args:
        user: User object to check/update
    """
    if not user.is_active:
        user.is_active = True


# ============================================================
# FastAPI Dependency (Async)
# ============================================================

async def get_current_user(
        token: str = Depends(oauth2_scheme),
        db: AsyncSession = Depends(get_async_db)
) -> User:
    """
    Extract and validate current user from JWT token.

    Args:
        token: JWT access token from Authorization header
        db: Async database session

    Returns:
        User object

    Raises:
        HTTPException: If token invalid or user not found
    """
    payload = decode_access_token(token)
    user_id = payload.get("user_id")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return user

