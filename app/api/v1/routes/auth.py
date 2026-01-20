from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.enums import AuthProviderEnum
from app.schemas.auth import GoogleAuthSchema, AppleAuthSchema, TokenResponse, SignOutResponse
from app.utils.apple_utils import verify_apple_token
from app.utils.google_utils import verify_google_token
from app.utils.auth_utils import (
    get_or_create_user,
    issue_tokens,
    validate_refresh_token,
    revoke_refresh_token,
)

router = APIRouter()


# ---------------------------
# Google Sign-In
# ---------------------------
@router.post("/google", response_model=TokenResponse)
def google_sign_in(payload: GoogleAuthSchema, db: Session = Depends(get_db)):
    try:
        idinfo = verify_google_token(payload.id_token)

        email = (idinfo.get("email") or "").lower().strip()
        if not email:
            raise HTTPException(status_code=400, detail="Google token missing email")

        user = get_or_create_user(
            email=email,
            provider=AuthProviderEnum.GOOGLE,
            payload={
                "name": payload.name,
                "picture": idinfo.get("picture") or payload.picture,
                "google_sub": idinfo.get("sub"),
                "google_picture": idinfo.get("picture"),
                # Security: ID token is verified but not stored
            },
            db=db,
        )

        return issue_tokens(user, db)

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid Google token")


# ---------------------------
# Apple Sign-In
# ---------------------------
@router.post("/apple", response_model=TokenResponse)
def apple_sign_in(payload: AppleAuthSchema, db: Session = Depends(get_db)):
    try:
        idinfo = verify_apple_token(payload.id_token)

        email = (idinfo.get("email") or "").lower().strip()
        if not email:
            raise HTTPException(status_code=400, detail="Apple token missing email")

        user = get_or_create_user(
            email=email,
            provider=AuthProviderEnum.APPLE,
            payload={
                "name": payload.name,
                "picture": payload.picture,
                # Security: ID token is verified but not stored
            },
            db=db,
        )

        return issue_tokens(user, db)

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid Apple token")


# ---------------------------
# Refresh Token API
# ---------------------------
@router.post("/refresh", response_model=TokenResponse)
def refresh_access_token(refresh_token: str, db: Session = Depends(get_db)):
    user = validate_refresh_token(refresh_token, db)
    return issue_tokens(user, db)


# ---------------------------
# Sign Out API
# ---------------------------
@router.post("/signout", response_model=SignOutResponse)
def sign_out(refresh_token: str, db: Session = Depends(get_db)):
    """Sign out a user by revoking their refresh token."""
    revoke_refresh_token(refresh_token, db)
    return SignOutResponse(detail="Successfully signed out")

