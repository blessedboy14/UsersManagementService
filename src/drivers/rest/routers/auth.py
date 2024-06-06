from typing import Annotated

from fastapi import (
    APIRouter,
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

from src.drivers.rest.routers.exceptions import ModelValidationError
from src.drivers.rest.routers.schema import (
    UserIn,
    TokenSchema,
    ResetPasswordRequest,
    ResponseUser,
    ResetPasswordResponse,
)
from src.drivers.rest.routers.config import logger
from src.domain.entities.user import LoginUser
from src.drivers.rest.dependencies import (
    get_sign_up_use_case,
    get_login_use_case,
    get_refresh_token_use_case,
    get_reset_password_use_case,
)
from src.use_cases.auth_use_cases import (
    CreateUserUseCase,
    LoginUseCase,
    RefreshTokenUseCase,
    ResetPasswordUseCase,
)

router = APIRouter()


@router.post(
    '/login',
    status_code=status.HTTP_200_OK,
    response_model=TokenSchema,
    summary='Login',
)
async def login(
    use_case: Annotated[LoginUseCase, Depends(get_login_use_case)],
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    user = LoginUser(login=form_data.username, password=form_data.password)
    return await use_case(user)


@router.post(
    '/signup',
    status_code=status.HTTP_201_CREATED,
    response_model=ResponseUser,
    summary='Sign Up',
)
async def signup(
    use_case: Annotated[CreateUserUseCase, Depends(get_sign_up_use_case)],
    username: Annotated[str, Form()],
    phone: Annotated[PhoneNumber, Form()],
    email: Annotated[EmailStr, Form()],
    password: Annotated[str, Form()],
    image: UploadFile = File(None),
):
    try:
        user_in = UserIn(email=email, phone=phone, password=password, username=username)
    except ValidationError as err:
        logger.error(f'failed to create model from sign up input with err: {err}')
        raise ModelValidationError(repr(err.errors()[0]['msg']))
    file_bytes = None if image is None else await image.read()
    return await use_case(user_in.to_entity(), file_bytes)


@router.post(
    '/refresh-token',
    status_code=status.HTTP_200_OK,
    response_model=TokenSchema,
    summary='Refresh Both Tokens',
)
async def refresh_token(
    use_case: Annotated[RefreshTokenUseCase, Depends(get_refresh_token_use_case)],
    refresh_tkn: Annotated[str, Header()],
):
    return await use_case(refresh_tkn)


@router.post(
    '/reset-password',
    status_code=status.HTTP_200_OK,
    response_model=ResetPasswordResponse,
    summary='Reset Your Password',
)
async def reset_password(
    request: ResetPasswordRequest,
    use_case: Annotated[ResetPasswordUseCase, Depends(get_reset_password_use_case)],
):
    return await use_case(request.email)
