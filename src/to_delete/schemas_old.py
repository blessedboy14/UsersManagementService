import uuid
import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict, model_validator
from pydantic_extra_types.phone_numbers import PhoneNumber
from typing import Optional
from enum import Enum

from src.domain.entities.user import RoleEnum


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
    username: str = Field(pattern='^[A-Za-z0-9-_]+$', min_length=3, max_length=40)
    phone: str = Field(min_length=13, max_length=13)
    email: EmailStr
    role: Optional[RoleEnum] = RoleEnum.USER
    group_id: Optional[uuid.UUID] = None
    image: Optional[str] = None
    is_blocked: bool = False
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now)
    modified_at: datetime.datetime = Field(default_factory=datetime.datetime.now)

    @model_validator(mode='after')
    def validate_time(self):
        self.modified_at = datetime.datetime.now()
        return self


class UserPatch(BaseModel):
    name: Optional[str] = None
    surname: Optional[str] = None
    username: Optional[str] = None
    phone: Optional[PhoneNumber] = None
    email: Optional[EmailStr] = None

    model_config = {
        'json_schema_extra': {
            'examples': [
                {
                    'name': 'John',
                    'surname': 'Doe',
                    'username': 'your_username',
                    'phone': '+375331234567',
                    'email': 'your@email.com',
                }
            ]
        }
    }


class OrderByEnum(str, Enum):
    ASC = 'asc'
    DESC = 'desc'


class AdminPatch(UserPatch):
    role: Optional[RoleEnum] = RoleEnum.USER
    is_blocked: Optional[bool] = False
    group_id: Optional[uuid.UUID] = None

    model_config = {
        'json_schema_extra': {
            'examples': [
                {
                    'name': 'John',
                    'surname': 'Doe',
                    'username': 'your_username',
                    'phone': '+375331234567',
                    'email': 'your@email.com',
                    'image': 's3://some_name/16.jpg',
                    'role': 'user',
                    'is_blocked': 'false',
                    'group_id': '869bd587-f1a7-4e42-88d4-86713f64f308',
                }
            ]
        }
    }
