import uuid
import datetime
from enum import Enum
from typing import Optional

from phonenumbers import PhoneNumber
from pydantic import BaseModel, Field, EmailStr, ConfigDict, model_validator

from src.domain.entities.user import RoleEnum, AuthUser as AuthUserModel

PhoneNumber.phone_format = 'E164'


class AuthUser(BaseModel):
    email: EmailStr = Field()
    username: str = Field(min_length=3, max_length=40)
    phone: PhoneNumber = Field()

    model_config = {
        'json_schema_extra': {
            'examples': [
                {
                    'email': 'your@email.com',
                    'username': 'your_username',
                    'phone': '+48221234567',
                    'password': 'your_password',
                }
            ]
        }
    }


class ResponseUser(AuthUser):
    message: str = Field(default='user created')


class ResetPasswordRequest(BaseModel):
    email: EmailStr = Field(min_length=3, max_length=128, examples=['your@email.com'])


class LoginUser(BaseModel):
    login: str = Field(
        min_length=3, max_length=64, examples=['<EMAIL>', '<USERNAME>', '+48221234567']
    )
    password: str = Field(min_length=8, max_length=128, examples=['your_password'])


class UserIn(AuthUser):
    model_config = ConfigDict(regex_engine='python-re')
    password: str = Field(
        pattern=r'[a-z0-9@#$%^&\'~\"+=_]{8,}', min_length=8, max_length=128
    )

    def to_entity(self) -> AuthUserModel:
        return AuthUserModel(
            email=self.email,
            username=self.username,
            phone_number=str(self.phone),
            password=self.password
        )


class UserInDB(AuthUser):
    hashed_password: str


class TokenSchema(BaseModel):
    access_token: str
    refresh_token: str
    type: str


class ResetPasswordMessage(BaseModel):
    user_id: uuid.UUID
    subject: str
    body: str
    email: EmailStr
    published_at: datetime.datetime


class ResetPasswordResponse(BaseModel):
    message: str
    email: str


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
