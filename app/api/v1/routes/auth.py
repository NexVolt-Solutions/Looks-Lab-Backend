"""
Authentication routes.
Handles OAuth sign-in, token refresh, and sign-out.
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_async_db
from app.core.logging import logger
from app.core.rate_limit import RateLimits, limiter
from app.enums import AuthProviderEnum
from app.schemas.auth import (
    AppleAuthSchema,
    GoogleAuthSchema,
    SignOutResponse,
    TokenResponse,
)
from app.services.auth_service import AuthService
from app.utils.apple_utils import verify_apple_token
from app.utils.google_utils import verify_google_token

router = APIRouter()


# ── Request Bodies ────────────────────────────────────────────────

class RefreshTokenRequest(BaseModel):
    refresh_token: str


class SignOutRequest(BaseModel):
    refresh_token: str


# ── Routes ────────────────────────────────────────────────────────

@router.post("/google", response_model=TokenResponse)
@limiter.limit(RateLimits.AUTH)
async def google_sign_in(
    request: Request,  # noqa: ARG001 — required by slowapi rate limiter
    payload: GoogleAuthSchema,
    db: AsyncSession = Depends(get_async_db)
):
    try:
        token_info = verify_google_token(payload.id_token)

        email = (token_info.get("email") or "").lower().strip()
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
                "picture": token_info.get("picture") or payload.picture,
                "google_sub": token_info.get("sub"),
                "google_picture": token_info.get("picture"),
                "last_google_id_token": payload.id_token,
            }
        )

        await auth_service.update_last_login(user.id)

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
        logger.error(
            f"Google sign-in failed: {e}",
            exc_info=settings.is_development
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed"
        )


@router.post("/apple", response_model=TokenResponse)
@limiter.limit(RateLimits.AUTH)
async def apple_sign_in(
    request: Request,  # noqa: ARG001 — required by slowapi rate limiter
    payload: AppleAuthSchema,
    db: AsyncSession = Depends(get_async_db)
):
    try:
        token_info = verify_apple_token(payload.id_token)

        email = (token_info.get("email") or "").lower().strip()
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
                "apple_sub": token_info.get("sub"),
                "last_apple_id_token": payload.id_token,
            }
        )

        await auth_service.update_last_login(user.id)

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
        logger.error(
            f"Apple sign-in failed: {e}",
            exc_info=settings.is_development
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed"
        )


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit(RateLimits.AUTH)
async def refresh_access_token(
    request: Request,  # noqa: ARG001 — required by slowapi rate limiter
    body: RefreshTokenRequest,
    db: AsyncSession = Depends(get_async_db)
):
    try:
        auth_service = AuthService(db)
        user = await auth_service.validate_refresh_token(body.refresh_token)
        return await auth_service.issue_tokens(user)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Token refresh failed: {e}",
            exc_info=settings.is_development
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )


@router.post("/sign-out", response_model=SignOutResponse)
@limiter.limit(RateLimits.AUTH)
async def sign_out(
    request: Request,  # noqa: ARG001 — required by slowapi rate limiter
    body: SignOutRequest,
    db: AsyncSession = Depends(get_async_db)
):
    try:
        auth_service = AuthService(db)
        await auth_service.revoke_refresh_token(body.refresh_token)
        return SignOutResponse(detail="Successfully signed out")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Sign out failed: {e}",
            exc_info=settings.is_development
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Sign out failed"
        )

