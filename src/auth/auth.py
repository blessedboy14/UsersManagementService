from typing import Annotated
from fastapi import (
    APIRouter,
    HTTPException,
    status,
    Depends,
    Form,
    UploadFile,
    File,
    Header,
)
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import EmailStr, ValidationError
from pydantic_extra_types.phone_numbers import PhoneNumber

from src.auth.schemas import (
    UserIn,
    LoginUser,
    TokenSchema,
    ResetPasswordRequest,
    ResponseUser,
    ResetPasswordResponse,
)
from src.config.settings import logger
from src.dependencies.core import DBSession, Redis
from src.auth.service import (
    login_user,
    refresh,
    create_new_user,
    send_reset_password_message,
)

router = APIRouter()


@router.post(
    '/login',
    status_code=status.HTTP_200_OK,
    response_model=TokenSchema,
    summary='Login',
)
async def login(session: DBSession, form_data: OAuth2PasswordRequestForm = Depends()):
    logger.info(f'login request from {form_data.username}')
    user = LoginUser(login=form_data.username, password=form_data.password)
    return await login_user(user, session)


@router.post(
    '/signup',
    status_code=status.HTTP_201_CREATED,
    response_model=ResponseUser,
    summary='Sign Up',
)
async def signup(
    username: Annotated[str, Form()],
    phone: Annotated[PhoneNumber, Form()],
    email: Annotated[EmailStr, Form()],
    password: Annotated[str, Form()],
    session: DBSession,
    image: UploadFile = File(None),
):
    logger.info(f'sign up request from {username}')
    try:
        userIn = UserIn(email=email, phone=phone, password=password, username=username)
    except ValidationError as err:
        logger.error(f'failed to create model from sign up input with err: {err}')
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=repr(err.errors()[0]['msg'])
        )
    return await create_new_user(userIn, session, image)


@router.post(
    '/refresh-token',
    status_code=status.HTTP_200_OK,
    response_model=TokenSchema,
    summary='Refresh Both Tokens',
)
async def refresh_token(redis: Redis, refresh_tkn: Annotated[str, Header()]):
    logger.info('refresh token request')
    return await refresh(refresh_tkn, redis)


@router.post(
    '/reset-password',
    status_code=status.HTTP_200_OK,
    response_model=ResetPasswordResponse,
    summary='Reset Your Password',
)
async def reset_password(request: ResetPasswordRequest, session: DBSession):
    logger.info(f'password reset request from {request.email}')
    return await send_reset_password_message(request, session)
