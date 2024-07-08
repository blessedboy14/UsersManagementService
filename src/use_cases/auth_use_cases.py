from datetime import datetime, timedelta

from src.common.security import (
    verify_password,
    get_password_hash,
    create_refresh_jwt,
    create_access_jwt,
    decode_token,
    create_link_token,
)
from src.domain.entities.reset_password_message import (
    ResetPasswordMessage,
    ResetPasswordResponse,
)
from src.domain.entities.token import Token
from src.domain.entities.user import User, LoginUser, AuthUser
from src.ports.publisher.message_publisher import MessagePublisher
from src.ports.repositories.images_repository import ImagesRepository
from src.ports.repositories.user_repository import UserRepository
from src.ports.repositories.token_repository import TokenRepository
from src.use_cases.exceptions import (
    UserNotFoundError,
    UserIsBlockedError,
    PasswordDoesNotMatchError,
    TokenIsBlacklistedError,
    NotARefreshTokenError,
    InvalidTokenError,
)


class CreateUserUseCase:
    def __init__(
        self, user_repository: UserRepository, image_repository: ImagesRepository
    ):
        self._user_repository = user_repository
        self._image_repository = image_repository

    async def _manage_file_uploading(self, content: bytes, email: str):
        created_user = await self._user_repository.get_by_email(email)
        s3_filename = await self._image_repository.upload_image(created_user, content)
        created_user.image = s3_filename
        await self._user_repository.partial_update(created_user)

    async def __call__(self, auth_user: AuthUser, image: bytes | None) -> User:
        hashed_password = get_password_hash(auth_user.password)
        user = User(
            email=auth_user.email,
            phone=auth_user.phone_number,
            username=auth_user.username,
            hashed_password=hashed_password,
        )
        user = await self._user_repository.create(user)
        if image is not None:
            await self._manage_file_uploading(image, user.email)
        return user


class LoginUseCase:
    def __init__(
        self, user_repository: UserRepository, token_repository: TokenRepository
    ):
        self._user_repository = user_repository
        self._token_repository = token_repository

    async def __call__(self, login_model: LoginUser) -> Token:
        database_user = await self._user_repository.get_by_login(login_model.login)
        if not database_user:
            raise UserNotFoundError(login_model.login)
        if database_user.is_blocked:
            raise UserIsBlockedError(database_user.id)
        if not verify_password(login_model.password, database_user.hashed_password):
            raise PasswordDoesNotMatchError(database_user.id)
        data = {'user_id': database_user.id.hex}
        refresh_token = create_refresh_jwt(data)
        await self._token_repository.set(database_user.id.hex, refresh_token)
        access_token = create_access_jwt(data)
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            type='bearer',
        )


class RefreshTokenUseCase:
    def __init__(
        self, user_repository: UserRepository, token_repository: TokenRepository
    ):
        self._user_repository = user_repository
        self._token_repository = token_repository

    async def _is_token_valid(self, token: str, user_id: str):
        return (await self._token_repository.get(user_id)) == token

    async def _blacklist_token(self, token: str):
        await self._token_repository.blacklist(token)

    async def __call__(self, refresh_token: str) -> Token:
        payload = decode_token(refresh_token)
        user_id = payload.get('user_id')
        if not (await self._is_token_valid(refresh_token, user_id)):
            raise TokenIsBlacklistedError()
        token_mode = payload.get('mode')
        if token_mode and token_mode == 'refresh_token':
            await self._token_repository.remove(user_id)
            data = {'user_id': user_id}
            access_token = create_access_jwt(data)
            refresh_token = create_refresh_jwt(data)
            await self._token_repository.set(user_id, refresh_token)
            return Token(
                access_token=access_token,
                refresh_token=refresh_token,
                type='bearer',
            )
        else:
            raise NotARefreshTokenError()


class ResetPasswordUseCase:
    def __init__(self, user_repository: UserRepository, publisher: MessagePublisher):
        self._user_repository = user_repository
        self._message_publisher = publisher

    @staticmethod
    def _generate_reset_password_url(email: str, user_id: str):
        payload = {
            'email': email,
            'type': 'reset_password',
            'expiry': (datetime.utcnow() + timedelta(days=30)).isoformat(),
        }
        # logger.debug(f'generating reset password link for: {email}')
        token = create_link_token(payload)
        reset_link = (
            f'https://127.0.0.1:8000/auth/reset-password/{user_id}?token=' + token
        )
        return reset_link

    async def __call__(self, email: str) -> ResetPasswordResponse:
        user = await self._user_repository.get_by_email(email)
        if not user:
            raise UserNotFoundError(email)
        message = ResetPasswordMessage(
            user_id=str(user.id),
            subject=f'Resetting Password To Your Account: {email}',
            body='Click this link to reset your password '
            f'{self._generate_reset_password_url(email, str(user.id))}',
            email=email,
            published_at=datetime.utcnow().isoformat(),
        )
        self._message_publisher.publish(message)
        return ResetPasswordResponse(
            message='Reset link was sent to your email', email=email
        )


class AuthUserWithJWTUseCase:
    def __init__(self, user_repository: UserRepository):
        self._user_repository = user_repository

    async def __call__(self, access_token: str) -> User:
        payload = decode_token(access_token)
        user_id = payload.get('user_id')
        if user_id is None:
            raise InvalidTokenError('Token invalid')
        user = await self._user_repository.get_by_id(user_id)
        if user is None:
            raise InvalidTokenError("User don't exist")
        return user
