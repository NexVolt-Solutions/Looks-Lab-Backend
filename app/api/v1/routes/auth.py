from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.core.config import settings
from app.core.logging import logger
from app.core.rate_limit import RateLimits, limiter
from app.enums import AuthProviderEnum
from app.schemas.auth import AppleAuthSchema, GoogleAuthSchema, SignOutResponse, TokenResponse
from app.services.auth_service import AuthService
from app.utils.apple_utils import verify_apple_token
from app.utils.google_utils import verify_google_token

router = APIRouter()


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class SignOutRequest(BaseModel):
    refresh_token: str


@router.post("/google", response_model=TokenResponse)
@limiter.limit(RateLimits.AUTH)
async def google_sign_in(
    request: Request,
    payload: GoogleAuthSchema,
    db: AsyncSession = Depends(get_async_db),
):
    try:
        idinfo = verify_google_token(payload.id_token)

        email = (idinfo.get("email") or "").lower().strip()
        if not email:
            raise HTTPException(status_code=400, detail="Google token missing email")

        auth_service = AuthService(db)
        user, is_new_user = await auth_service.get_or_create_user(
            email=email,
            provider=AuthProviderEnum.GOOGLE,
            payload={
                "name": payload.name,
                "picture": idinfo.get("picture") or payload.picture,
                "google_sub": idinfo.get("sub"),
                "google_picture": idinfo.get("picture"),
                "last_google_id_token": payload.id_token,
            }
        )
        await auth_service.update_last_login(user.id)
        return await auth_service.issue_tokens(user, is_new_user=is_new_user)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Google sign-in failed: {e}", exc_info=settings.is_development)
        raise HTTPException(status_code=500, detail="Authentication failed")


@router.post("/apple", response_model=TokenResponse)
@limiter.limit(RateLimits.AUTH)
async def apple_sign_in(
    request: Request,
    payload: AppleAuthSchema,
    db: AsyncSession = Depends(get_async_db),
):
    try:
        token_info = await verify_apple_token(payload.id_token)

        email = (token_info.get("email") or "").lower().strip()
        if not email:
            raise HTTPException(status_code=400, detail="Apple token missing email")

        auth_service = AuthService(db)
        user, is_new_user = await auth_service.get_or_create_user(
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
        return await auth_service.issue_tokens(user, is_new_user=is_new_user)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Apple sign-in failed: {e}", exc_info=settings.is_development)
        raise HTTPException(status_code=500, detail="Authentication failed")


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit(RateLimits.AUTH)
async def refresh_access_token(
    request: Request,
    body: RefreshTokenRequest,
    db: AsyncSession = Depends(get_async_db),
):
    try:
        auth_service = AuthService(db)
        user = await auth_service.validate_refresh_token(body.refresh_token)
        return await auth_service.issue_tokens(user, is_new_user=False)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh failed: {e}", exc_info=settings.is_development)
        raise HTTPException(status_code=500, detail="Token refresh failed")


@router.post("/sign-out", response_model=SignOutResponse)
@limiter.limit(RateLimits.AUTH)
async def sign_out(
    request: Request,
    body: SignOutRequest,
    db: AsyncSession = Depends(get_async_db),
):
    try:
        await AuthService(db).revoke_refresh_token(body.refresh_token)
        return SignOutResponse(detail="Successfully signed out")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Sign out failed: {e}", exc_info=settings.is_development)
        raise HTTPException(status_code=500, detail="Sign out failed")
        
        