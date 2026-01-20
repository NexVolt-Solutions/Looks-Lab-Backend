from pydantic import BaseModel, EmailStr

class UserBase(BaseModel):
    id: int
    email: EmailStr

    model_config = {"from_attributes": True}

