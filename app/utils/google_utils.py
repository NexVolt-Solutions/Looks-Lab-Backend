"""
Google Sign-In utilities.
Handles Google identity token verification using Google's OAuth2 library.
"""
from google.auth.exceptions import GoogleAuthError
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from fastapi import HTTPException, status as http_status

from app.core.config import settings
from app.core.logging import logger

# ── Constants ─────────────────────────────────────────────────────
GOOGLE_ISSUERS = {"accounts.google.com", "https://accounts.google.com"}

# Cache for Google request object
_google_request: google_requests.Request | None = None


# ── Request Object Management ─────────────────────────────────────
def get_google_request() -> google_requests.Request:
    """
    Return a cached Google request object for token verification.
    Reuses the same request object to avoid creating new ones each time.
    """
    global _google_request
    if _google_request is None:
        _google_request = google_requests.Request()
        logger.debug("Created new Google request object")
    return _google_request


# ── Token Verification ────────────────────────────────────────────
def verify_google_token(identity_token: str) -> dict:
    """
    Verify Google identity token and return decoded claims.

    Args:
        identity_token: Google Sign-In identity token

    Returns:
        Decoded token payload with user claims

    Raises:
        HTTPException: If token is invalid or verification fails
    """
    try:
        idinfo = id_token.verify_oauth2_token(
            identity_token,
            get_google_request(),
            settings.GOOGLE_CLIENT_ID,
        )

        # Verify issuer (safer check to avoid trailing slash mismatch)
        iss = idinfo.get("iss", "")
        if not any(iss.startswith(valid) for valid in GOOGLE_ISSUERS):
            logger.warning(f"Invalid Google token issuer: {iss}")
            raise HTTPException(
                status_code=http_status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token issuer"
            )

        logger.info(
            f"Google token verified successfully for email: {idinfo.get('email')}, aud={idinfo.get('aud')}"
        )
        return idinfo

    except GoogleAuthError as e:
        logger.error(f"Google auth error during token verification: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Google identity token: {e}"
        )
    except ValueError as e:
        logger.error(f"ValueError during Google token verification: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Google identity token: {e}"
        )
    except Exception as e:
        logger.error(f"Unexpected error verifying Google token: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google token verification failed"
        )

