"""
Apple Sign-In utilities.
Handles Apple identity token verification using Apple's public keys.
"""
from datetime import datetime, timedelta, timezone

import requests
from fastapi import HTTPException
from fastapi import status as http_status
from jose import jwt, JWTError

from app.core.config import settings
from app.core.logging import logger


# ── Constants ─────────────────────────────────────────────────────

APPLE_KEYS_URL = "https://appleid.apple.com/auth/keys"
APPLE_ISSUER = "https://appleid.apple.com"

# Cache for Apple public keys
_cached_keys: list[dict] | None = None
_cached_at: datetime | None = None
_CACHE_TTL = timedelta(hours=12)


# ── Public Key Management ─────────────────────────────────────────

def get_apple_public_keys() -> list[dict]:
    """
    Fetch Apple public keys used to verify identity tokens.
    Keys are cached for 12 hours to reduce API calls.

    Returns:
        List of Apple public key dictionaries

    Raises:
        HTTPException: If unable to fetch keys from Apple
    """
    global _cached_keys, _cached_at

    # Return cached keys if still valid
    if _cached_keys and _cached_at:
        age = datetime.now(timezone.utc) - _cached_at
        if age < _CACHE_TTL:
            return _cached_keys

    # Fetch fresh keys from Apple
    try:
        response = requests.get(APPLE_KEYS_URL, timeout=10)
        response.raise_for_status()

        keys = response.json()["keys"]
        _cached_keys = keys
        _cached_at = datetime.now(timezone.utc)

        logger.info("Refreshed Apple public keys from server")
        return keys

    except requests.RequestException as e:
        logger.error(f"Failed to fetch Apple public keys: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to fetch Apple public keys"
        )


# ── Token Verification ────────────────────────────────────────────

def verify_apple_token(identity_token: str) -> dict:
    """
    Verify Apple identity token (JWT) and return decoded claims.

    Args:
        identity_token: Apple Sign-In identity token

    Returns:
        Decoded token payload with user claims

    Raises:
        HTTPException: If token is invalid or verification fails
    """
    keys = get_apple_public_keys()

    # Try each key until one works
    for key in keys:
        try:
            decoded = jwt.decode(
                identity_token,
                key,
                algorithms=["RS256"],
                audience=settings.APPLE_CLIENT_ID,
                issuer=APPLE_ISSUER,
            )
            logger.info(f"Apple token verified successfully for sub: {decoded.get('sub')}")
            return decoded

        except JWTError:
            continue  # Try next key

    # No key worked — token is invalid
    logger.warning("Invalid Apple identity token — all keys failed")
    raise HTTPException(
        status_code=http_status.HTTP_401_UNAUTHORIZED,
        detail="Invalid Apple identity token"
    )

