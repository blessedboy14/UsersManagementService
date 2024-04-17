import uuid
import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from enum import Enum


class RoleEnum(str, Enum):
    ADMIN = "admin"
    MODERATOR = "moderator"
    USER = "user"

    class Config:
        from_attributes = True


class Group(BaseModel):

    id: uuid.UUID
    name: str
    created: datetime.datetime

    class Config:
        from_attributes = True


class User(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: Optional[str] = Field("John", min_length=3, max_length=128)
    surname: Optional[str] = Field("Doe", min_length=3, max_length=128)
    username: str = Field(min_length=3, max_length=128)
    phone: str = Field(min_length=13, max_length=13)
    email: EmailStr
    role: Optional[RoleEnum] = RoleEnum.USER
    group_id: uuid.UUID
    image: Optional[str] = "s3://bucket-name/path/to/file"
    is_blocked: bool = False
    hashed_password: str
    created_at: datetime.datetime
    modified_at: datetime.datetime
