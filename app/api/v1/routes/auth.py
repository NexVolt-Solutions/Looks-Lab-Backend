"""
Authentication routes.
Handles OAuth sign-in, token refresh, and sign-out.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.enums import AuthProviderEnum
from app.schemas.auth import GoogleAuthSchema, AppleAuthSchema, TokenResponse, SignOutResponse
from app.services.auth_service import AuthService
from app.utils.apple_utils import verify_apple_token
from app.utils.google_utils import verify_google_token
from app.core.logging import logger

router = APIRouter()


@router.post("/google", response_model=TokenResponse)
async def google_sign_in(payload: GoogleAuthSchema, db: AsyncSession = Depends(get_async_db)):
    try:
        idinfo = verify_google_token(payload.id_token)

        email = (idinfo.get("email") or "").lower().strip()
        if not email:
            logger.warning("Google token missing email")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Google token missing email"
            )

        auth_service = AuthService(db)

        user = await auth_service.get_or_create_user(
            email=email,
            provider=AuthProviderEnum.GOOGLE,
            payload={
                "name": payload.name,
                "picture": idinfo.get("picture") or payload.picture,
                "google_sub": idinfo.get("sub"),
                "google_picture": idinfo.get("picture"),
            }
        )

        return await auth_service.issue_tokens(user)

    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Google token verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Google token"
        )
    except Exception as e:
        logger.error(f"Google sign-in failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed"
        )


@router.post("/apple", response_model=TokenResponse)
async def apple_sign_in(payload: AppleAuthSchema, db: AsyncSession = Depends(get_async_db)):
    try:
        idinfo = verify_apple_token(payload.id_token)

        email = (idinfo.get("email") or "").lower().strip()
        if not email:
            logger.warning("Apple token missing email")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Apple token missing email"
            )

        auth_service = AuthService(db)

        user = await auth_service.get_or_create_user(
            email=email,
            provider=AuthProviderEnum.APPLE,
            payload={
                "name": payload.name,
                "picture": payload.picture,
            }
        )

        return await auth_service.issue_tokens(user)

    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Apple token verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Apple token"
        )
    except Exception as e:
        logger.error(f"Apple sign-in failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed"
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_access_token(refresh_token: str, db: AsyncSession = Depends(get_async_db)):
    try:
        auth_service = AuthService(db)

        user = await auth_service.validate_refresh_token(refresh_token)
        return await auth_service.issue_tokens(user)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )


@router.post("/signout", response_model=SignOutResponse)
async def sign_out(refresh_token: str, db: AsyncSession = Depends(get_async_db)):
    try:
        auth_service = AuthService(db)
        await auth_service.revoke_refresh_token(refresh_token)

        return SignOutResponse(detail="Successfully signed out")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Sign out failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Sign out failed"
        )

