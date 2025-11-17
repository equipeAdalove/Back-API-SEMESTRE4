# schemas/user_schemas.py
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    name: str = Field(..., min_length=2, max_length=100)
    password: str = Field(..., min_length=6, max_length=128)


class User(BaseModel):
    id: int
    nome: str
    email: EmailStr

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


class UserProfile(BaseModel):
    name: str
    email: EmailStr


class TokenResponseData(BaseModel):
    access_token: str
    token_type: str


class TokenResponse(BaseModel):
    data: TokenResponseData
