import requests
from jose import jwt, jwk
from jose.utils import base64url_decode
from fastapi import HTTPException, status
from app.core.config import settings
from datetime import datetime, timedelta, timezone

APPLE_KEYS_URL = "https://appleid.apple.com/auth/keys"
APPLE_ISSUER = "https://appleid.apple.com"

# Cache for Apple public keys
_cached_keys = None
_cached_at: datetime | None = None
_cache_ttl = timedelta(hours=12)  # refresh keys every 12 hours


def get_apple_public_keys():
    """
    Fetch Apple public keys used to verify identity tokens.
    Cached for efficiency.
    """
    global _cached_keys, _cached_at

    if _cached_keys and _cached_at and datetime.now(timezone.utc) - _cached_at < _cache_ttl:
        return _cached_keys

    response = requests.get(APPLE_KEYS_URL, timeout=5)
    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to fetch Apple public keys"
        )

    _cached_keys = response.json()["keys"]
    _cached_at = datetime.now(timezone.utc)
    return _cached_keys


def verify_apple_token(identity_token: str) -> dict:
    """
    Verify Apple identity token (JWT) and return decoded claims.
    """
    keys = get_apple_public_keys()

    for key in keys:
        try:
            decoded = jwt.decode(
                identity_token,
                key,
                algorithms=["RS256"],
                audience=settings.apple_client_id,
                issuer=APPLE_ISSUER
            )
            return decoded
        except jwt.JWTError:
            continue

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid Apple identity token"
    )

