from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from fastapi import HTTPException, status
from app.core.config import settings

# Cache for Google request object
_google_request = None


def get_google_request():
    """
    Return a cached Google request object for token verification.
    """
    global _google_request
    if _google_request is None:
        _google_request = google_requests.Request()
    return _google_request


def verify_google_token(identity_token: str) -> dict:
    """
    Verify Google identity token and return decoded claims.
    """
    try:
        idinfo = id_token.verify_oauth2_token(
            identity_token,
            get_google_request(),
            settings.google_client_id,
        )

        if idinfo["iss"] not in ["accounts.google.com", "https://accounts.google.com"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid issuer"
            )

        return idinfo

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Google identity token"
        )

