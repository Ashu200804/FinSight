from pydantic import BaseModel, EmailStr
from app.models.user import UserRole
from datetime import datetime
from typing import Optional

class UserSignup(BaseModel):
    email: EmailStr
    password: str
    role: Optional[UserRole] = UserRole.CREDIT_ANALYST

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    role: UserRole
    created_at: datetime

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse
