import uuid
from typing import Optional

from pydantic import BaseModel, EmailStr, Field
from pydantic_extra_types.phone_numbers import PhoneNumber


class AuthUser(BaseModel):
    email: EmailStr = Field(default="example@example.com")
    username: str = Field(min_length=3, max_length=128)
    phone: PhoneNumber = Field(default="+375291234567")


class LoginUser(BaseModel):
    login: str = Field(min_length=3, max_length=128)
    password: str = Field(min_length=8, max_length=128)


class UserIn(AuthUser):
    password: str = Field(min_length=8, max_length=128)


class UserInDB(AuthUser):
    hashed_password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    id: uuid.UUID | None = None
