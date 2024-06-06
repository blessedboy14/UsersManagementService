from typing import Annotated

from fastapi import Depends

from src.adapters.publisher.rabbitmq_publisher import RabbitMQMessagePublisher
from src.adapters.repositories.images_repository import AWSS3ImagesRepository
from src.adapters.repositories.token_repository import RedisTokenRepository
from src.dependencies.core import DBSession, Redis
from src.ports.publisher.message_publisher import MessagePublisher
from src.ports.repositories.images_repository import ImagesRepository
from src.ports.repositories.token_repository import TokenRepository
from src.ports.repositories.user_repository import UserRepository
from src.use_cases.auth_use_cases import (
    CreateUserUseCase,
    LoginUseCase,
    RefreshTokenUseCase,
    ResetPasswordUseCase,
    AuthUserWithJWTUseCase,
)
from src.adapters.repositories.user_repository import PostgreUserRepository
from src.config.settings import rabbit_config
from src.use_cases.users_use_cases import (
    PatchMeUseCase,
    DeleteMeUseCase,
    GetUserByIdUseCase,
    PatchUserByIdUseCase,
    DeleteUserByIdUseCase,
    ListUsersUseCase,
    UploadImageUseCase,
)


def get_users_repository(session: DBSession) -> UserRepository:
    return PostgreUserRepository(session)


def get_token_repository(redis: Redis) -> TokenRepository:
    return RedisTokenRepository(redis)


def get_message_publisher() -> MessagePublisher:
    return RabbitMQMessagePublisher(rabbit_config)


def get_images_repository() -> ImagesRepository:
    return AWSS3ImagesRepository()


def get_sign_up_use_case(
    users_repository: Annotated[UserRepository, Depends(get_users_repository)],
    images_repository: Annotated[ImagesRepository, Depends(get_images_repository)],
) -> CreateUserUseCase:
    return CreateUserUseCase(users_repository, images_repository)


def get_login_use_case(
    users_repository: Annotated[UserRepository, Depends(get_users_repository)],
) -> LoginUseCase:
    return LoginUseCase(users_repository)


def get_refresh_token_use_case(
    users_repository: Annotated[UserRepository, Depends(get_users_repository)],
    token_repository: Annotated[TokenRepository, Depends(get_token_repository)],
) -> RefreshTokenUseCase:
    return RefreshTokenUseCase(users_repository, token_repository)


def get_reset_password_use_case(
    users_repository: Annotated[UserRepository, Depends(get_users_repository)],
    publisher: Annotated[MessagePublisher, Depends(get_message_publisher)],
) -> ResetPasswordUseCase:
    return ResetPasswordUseCase(users_repository, publisher)


def get_patch_me_use_case(
    users_repository: Annotated[UserRepository, Depends(get_users_repository)],
) -> PatchMeUseCase:
    return PatchMeUseCase(users_repository)


def get_delete_me_use_case(
    users_repository: Annotated[UserRepository, Depends(get_users_repository)],
) -> DeleteMeUseCase:
    return DeleteMeUseCase(users_repository)


def get_get_user_by_id_use_case(
    users_repository: Annotated[UserRepository, Depends(get_users_repository)],
) -> GetUserByIdUseCase:
    return GetUserByIdUseCase(users_repository)


def get_patch_user_by_id_use_case(
    users_repository: Annotated[UserRepository, Depends(get_users_repository)],
) -> PatchUserByIdUseCase:
    return PatchUserByIdUseCase(users_repository)


def get_delete_user_by_id_use_case(
    users_repository: Annotated[UserRepository, Depends(get_users_repository)],
) -> DeleteUserByIdUseCase:
    return DeleteUserByIdUseCase(users_repository)


def get_list_users_use_case(
    users_repository: Annotated[UserRepository, Depends(get_users_repository)],
) -> ListUsersUseCase:
    return ListUsersUseCase(users_repository)


def get_delete_by_id_use_case(
    users_repository: Annotated[UserRepository, Depends(get_users_repository)],
) -> DeleteUserByIdUseCase:
    return DeleteUserByIdUseCase(users_repository)


def get_upload_file_use_case(
    users_repository: Annotated[UserRepository, Depends(get_users_repository)],
    images_repository: Annotated[ImagesRepository, Depends(get_images_repository)],
) -> UploadImageUseCase:
    return UploadImageUseCase(images_repository, users_repository)


def get_auth_with_jwt_use_case(
    users_repository: Annotated[UserRepository, Depends(get_users_repository)],
) -> AuthUserWithJWTUseCase:
    return AuthUserWithJWTUseCase(users_repository)
