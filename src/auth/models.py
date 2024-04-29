from pydantic import BaseModel, EmailStr, Field, field_validator
from pydantic_extra_types.phone_numbers import PhoneNumber

PhoneNumber.phone_format = 'E164'
special_chars = '~`!@#$%^&*()_-+={[}]|\:;"\'<,>.?/'


class AuthUser(BaseModel):
    email: EmailStr = Field(default='example@example.com')
    username: str = Field(pattern='^[A-Za-z0-9-_]+$', min_length=3, max_length=40)
    phone: PhoneNumber = Field(default='+375291234567')

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
    password: str = Field(min_length=8, max_length=128, examples=['your_password'])

    @field_validator('password')
    def check_password(cls, v):
        v = str(v)
        if (
            not any(c.islower() for c in v)
            or not any(c.isdigit() for c in v)
            or not any(c in special_chars for c in v)
        ):
            raise ValueError(
                'Password should contain at least 1 digit '
                f'1 character from (a-z) and 1 special character from {special_chars}'
            )
        return v


class UserInDB(AuthUser):
    hashed_password: str


class TokenSchema(BaseModel):
    message: str
    access_token: str
    refresh_token: str
    type: str


class ResetResponseSchema(BaseModel):
    message: str
    email: EmailStr
