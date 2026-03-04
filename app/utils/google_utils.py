from typing import Optional

from fastapi import HTTPException
from fastapi import status as http_status
from google.auth.exceptions import GoogleAuthError
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

from app.core.config import settings
from app.core.logging import logger

GOOGLE_ISSUERS = {"accounts.google.com", "https://accounts.google.com"}

_google_request: Optional[google_requests.Request] = None


def get_google_request() -> google_requests.Request:
    global _google_request
    if _google_request is None:
        _google_request = google_requests.Request()
    return _google_request


def verify_google_token(identity_token: str) -> dict:
    try:
        idinfo = id_token.verify_oauth2_token(
            identity_token,
            get_google_request(),
            settings.GOOGLE_CLIENT_ID,
        )

        iss = idinfo.get("iss", "")
        if not any(iss.startswith(v) for v in GOOGLE_ISSUERS):
            logger.warning(f"Invalid Google token issuer: {iss}")
            raise HTTPException(status_code=http_status.HTTP_401_UNAUTHORIZED, detail="Invalid token issuer")

        return idinfo

    except HTTPException:
        raise
    except (GoogleAuthError, ValueError) as e:
        logger.error(f"Google token verification failed: {e}")
        raise HTTPException(status_code=http_status.HTTP_401_UNAUTHORIZED, detail=f"Invalid Google identity token: {e}")
    except Exception as e:
        logger.error(f"Unexpected error verifying Google token: {e}")
        raise HTTPException(status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Google token verification failed")

