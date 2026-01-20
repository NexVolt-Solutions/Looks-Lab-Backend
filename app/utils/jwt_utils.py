from jose import jwt, JWTError, ExpiredSignatureError
from datetime import datetime, timedelta
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from uuid import uuid4

from app.core.config import settings
from app.core.database import get_db
from app.models.user import User

# ---------------------------
# Config
# ---------------------------
SECRET = settings.JWT_SECRET
ALGORITHM = settings.JWT_ALGORITHM
EXPIRATION_MINUTES = settings.JWT_EXPIRATION_MINUTES
REFRESH_DAYS = settings.REFRESH_TOKEN_EXPIRATION_DAYS

# ---------------------------
# Internal Helpers
# ---------------------------
def _create_token(data: dict, expires_minutes: int) -> str:
    """
    Create a JWT with an expiration timestamp.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=expires_minutes)
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    return jwt.encode(to_encode, SECRET, algorithm=ALGORITHM)


def _decode_token(token: str) -> dict:
    """
    Decode and validate a JWT, raising proper HTTP errors.
    """
    try:
        return jwt.decode(token, SECRET, algorithms=[ALGORITHM])
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

# ---------------------------
# Access Token
# ---------------------------
def create_access_token(data: dict) -> str:
    """Create a short-lived access token."""
    return _create_token(data, expires_minutes=EXPIRATION_MINUTES)


def decode_access_token(token: str) -> dict:
    """Decode and validate an access token."""
    return _decode_token(token)

# ---------------------------
# Refresh Token
# ---------------------------
def create_refresh_token() -> str:
    """Generate a secure opaque refresh token."""
    return str(uuid4())


def get_refresh_expiry() -> datetime:
    """Return UTC expiry timestamp for refresh token."""
    return datetime.utcnow() + timedelta(days=REFRESH_DAYS)

# ---------------------------
# User Activation Helper
# ---------------------------
def ensure_user_active(user: User) -> None:
    """Ensure the user account is active."""
    if not user.is_active:
        user.is_active = True

# ---------------------------
# FastAPI Dependency
# ---------------------------
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/google")  # adjust if needed

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """
    Dependency that extracts the current user from the JWT access token.
    """
    payload = decode_access_token(token)
    user_id = payload.get("user_id")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return user

