from pydantic import BaseModel, EmailStr, validator
from typing import Optional

class SignupRequest(BaseModel):
    username: str
    email: EmailStr
    phone_number: str
    password: str

    @validator('password')
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if len(v.encode("utf-8")) > 72:
            raise ValueError('Password too long (max 72 bytes)')
        return v

    @validator('phone_number')
    def phone_format(cls, v):
        if not v.isdigit() or len(v) != 10:
            raise ValueError('Phone number must be 10 digits')
        return v

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    phone_number: str

