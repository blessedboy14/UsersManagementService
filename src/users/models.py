import uuid
import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict, model_validator
from pydantic_extra_types.phone_numbers import PhoneNumber
from typing import Optional
from enum import Enum


class RoleEnum(str, Enum):
    ADMIN = "admin"
    MODERATOR = "moderator"
    USER = "user"


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

    @model_validator(mode="after")
    def validate_time(self):
        if self.modified_at:
            self.modified_at = datetime.datetime.now()
        else:
            self.modified_at = self.created_at
        return self


class User(UserBase):
    hashed_password: str


class UserPatch(BaseModel):

    name: Optional[str] = None
    surname: Optional[str] = None
    username: Optional[str] = None
    phone: Optional[PhoneNumber] = None
    email: Optional[EmailStr] = None
    image: Optional[str] = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "John",
                    "surname": "Doe",
                    "username": "your_username",
                    "phone": "+375331234567",
                    "email": "your@email.com",
                    "image": "path/to/image.jpg"
                }
            ]
        }
    }


class AdminPatch(UserPatch):
    role: Optional[RoleEnum] = RoleEnum.USER
    is_blocked: Optional[bool] = False
    group_id: Optional[uuid.UUID] = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "John",
                    "surname": "Doe",
                    "username": "your_username",
                    "phone": "+375331234567",
                    "email": "your@email.com",
                    "image": "path/to/image.jpg",
                    "role": "user",
                    "is_blocked": "false",
                    "group_id": "869bd587-f1a7-4e42-88d4-86713f64f308"
                }
            ]
        }
    }
