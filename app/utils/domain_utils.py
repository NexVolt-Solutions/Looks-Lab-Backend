from fastapi import HTTPException
from fastapi import status as http_status

from app.enums import DomainEnum


def validate_domain(domain: str) -> None:
    if domain not in DomainEnum.values():
        raise HTTPException(
            status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid domain. Must be one of: {', '.join(DomainEnum.values())}"
        )

