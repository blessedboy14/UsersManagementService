from pydantic import BaseModel, EmailStr, Field
from pydantic_extra_types.phone_numbers import PhoneNumber


PhoneNumber.phone_format = 'E164'


class AuthUser(BaseModel):
    email: EmailStr = Field(default='example@example.com')
    username: str = Field(min_length=3, max_length=128)
    phone: PhoneNumber = Field(default='+375291234567')

    model_config = {
        'json_schema_extra': {
            'examples': [
                {
                    'email': 'your@email.com',
                    'username': 'your_username',
                    'phone': '+48221234567',
                    'password': 'your_password'
                }
            ]
        }
    }


class ResetPasswordRequest(BaseModel):
    email: EmailStr = Field(min_length=3, max_length=128, examples=['your@email.com'])


class LoginUser(BaseModel):
    login: str = Field(
        min_length=3, max_length=128, examples=['<EMAIL>', '<USERNAME>', '+48221234567']
    )
    password: str = Field(min_length=8, max_length=128, examples=['your_password'])


class UserIn(AuthUser):
    password: str = Field(min_length=8, max_length=128, examples=['your_password'])


class UserInDB(AuthUser):
    hashed_password: str


class TokenSchema(BaseModel):
    message: str
    access_token: str
    refresh_token: str
    type: str
