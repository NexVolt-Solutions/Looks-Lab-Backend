from typing import Optional
from pydantic import BaseModel, EmailStr
from app.schemas.user import UserOut


class GoogleAuthSchema(BaseModel):
    id_token: str
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    picture: Optional[str] = None


class AppleAuthSchema(BaseModel):
    id_token: str
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    picture: Optional[str] = None


class TokenResponse(BaseModel):
    user: UserOut
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: Optional[int] = None
    is_new_user: bool = False 

    model_config = {"from_attributes": True}


class SignOutResponse(BaseModel):
    detail: str
    
    