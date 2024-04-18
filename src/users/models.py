import uuid
import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from pydantic_extra_types.phone_numbers import PhoneNumber
from typing import Optional
from enum import Enum


class RoleEnum(str, Enum):
    ADMIN = "admin"
    MODERATOR = "moderator"
    USER = "user"

    class Config:
        from_attributes = True


class Group(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    created: datetime.datetime


class UserBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: Optional[str] = Field(None, min_length=3, max_length=128)
    surname: Optional[str] = Field(None, min_length=3, max_length=128)
    username: str = Field(min_length=3, max_length=128)
    phone: str = Field(min_length=13, max_length=13)
    email: EmailStr
    role: Optional[RoleEnum] = RoleEnum.USER
    group_id: uuid.UUID
    image: Optional[str] = None
    is_blocked: bool = False
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now)
    modified_at: datetime.datetime = Field(default_factory=datetime.datetime.now)


class User(UserBase):
    hashed_password: str


class UserPatch(BaseModel):

    name: Optional[str] = None
    surname: Optional[str] = None
    username: Optional[str] = None
    phone: Optional[PhoneNumber] = None
    email: Optional[EmailStr] = None
    role: Optional[RoleEnum] = None
    image: Optional[str] = None
    is_blocked: Optional[bool] = None
