from pydantic import BaseModel, EmailStr
from typing import Optional


class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RegistrationResponse(BaseModel):
    message: str
    email: str
    requires_confirmation: bool
    access_token: Optional[str] = None


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str

