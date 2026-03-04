from datetime import datetime, timedelta, timezone
from typing import Optional

import httpx
from fastapi import HTTPException
from fastapi import status as http_status
from jose import jwt, JWTError

from app.core.config import settings
from app.core.logging import logger

APPLE_KEYS_URL = "https://appleid.apple.com/auth/keys"
APPLE_ISSUER = "https://appleid.apple.com"
_CACHE_TTL = timedelta(hours=12)

_cached_keys: Optional[list[dict]] = None
_cached_at: Optional[datetime] = None


async def get_apple_public_keys() -> list[dict]:
    global _cached_keys, _cached_at

    if _cached_keys and _cached_at and (datetime.now(timezone.utc) - _cached_at) < _CACHE_TTL:
        return _cached_keys

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(APPLE_KEYS_URL)
            response.raise_for_status()
        _cached_keys = response.json()["keys"]
        _cached_at = datetime.now(timezone.utc)
        logger.info("Refreshed Apple public keys")
        return _cached_keys
    except httpx.HTTPError as e:
        logger.error(f"Failed to fetch Apple public keys: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to fetch Apple public keys"
        )


async def verify_apple_token(identity_token: str) -> dict:
    keys = await get_apple_public_keys()

    for key in keys:
        try:
            return jwt.decode(
                identity_token,
                key,
                algorithms=["RS256"],
                audience=settings.APPLE_CLIENT_ID,
                issuer=APPLE_ISSUER,
            )
        except JWTError:
            continue

    logger.warning("Apple identity token verification failed — all keys exhausted")
    raise HTTPException(
        status_code=http_status.HTTP_401_UNAUTHORIZED,
        detail="Invalid Apple identity token"
    )

