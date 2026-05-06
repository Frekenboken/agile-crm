from pydantic import BaseModel, EmailStr
from uuid import UUID
from typing import Optional

class CurrentUserResponse(BaseModel):
    id: UUID
    email: EmailStr

class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    first_name: str
    last_name: str
    avatar_url: Optional[str] = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
    expires_in: int