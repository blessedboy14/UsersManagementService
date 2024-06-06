import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, ConfigDict
from pydantic_extra_types.phone_numbers import PhoneNumber

from src.domain.entities.user import AuthUser as AuthUserModel
from src.domain.entities.user import User

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
            phone_number=self.phone,
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
    published_at: datetime


class ResetPasswordResponse(BaseModel):
    message: str
    email: str
