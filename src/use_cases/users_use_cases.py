from dataclasses import replace

from src.domain.entities.user import User
from src.ports.repositories.images_repository import ImagesRepository
from src.ports.repositories.user_repository import UserRepository
from src.use_cases.exceptions import EmptyUpdateDataError, MethodNotAllowedError, UserNotFoundError
from src.to_delete.schemas_old import RoleEnum


class PatchMeUseCase:
    def __init__(self, user_repository: UserRepository):
        self._user_repository = user_repository

    async def __call__(self, updated_user: dict | None, current_user: User) -> User:
        if not updated_user:
            raise EmptyUpdateDataError(current_user.id)
        updated_model = replace(current_user, **updated_user)
        return await self._user_repository.partial_update(updated_model)


class DeleteMeUseCase:
    def __init__(self, user_repository: UserRepository):
        self._user_repository = user_repository

    async def __call__(self, current_user: User) -> None:
        await self._user_repository.delete(str(current_user.id))


class DeleteUserByIdUseCase:
    def __init__(self, user_repository: UserRepository):
        self._user_repository = user_repository

    async def __call__(self, current_user: User, user_id: str) -> None:
        if current_user.role is RoleEnum.ADMIN:
            await self._user_repository.delete(user_id)
        else:
            raise MethodNotAllowedError(current_user.id)


class PatchUserByIdUseCase:
    def __init__(self, user_repository: UserRepository):
        self._user_repository = user_repository

    async def __call__(self, current_user: User, user_id: str, updated_user: dict | None) -> User:
        if current_user.role is not RoleEnum.ADMIN:
            raise MethodNotAllowedError(current_user.id)
        if not updated_user:
            raise EmptyUpdateDataError(current_user.id)
        requested_user = await self._user_repository.get_by_id(user_id)
        if requested_user:
            updated_model = replace(requested_user, **updated_user)
            return await self._user_repository.partial_update(updated_model)
        else:
            raise UserNotFoundError(user_id)


class GetUserByIdUseCase:
    def __init__(self, user_repository: UserRepository):
        self._user_repository = user_repository

    async def __call__(self, current_user: User, user_id: str) -> User:
        if current_user.role is RoleEnum.USER:
            raise MethodNotAllowedError(current_user.id)
        user = await self._user_repository.get_by_id(user_id)
        if user:
            if current_user.role is RoleEnum.MODERATOR and user.group == current_user.group:
                return user
            elif current_user.role is RoleEnum.ADMIN:
                return user
        else:
            raise UserNotFoundError(user_id)


class ListUsersUseCase:
    def __init__(self, user_repository: UserRepository):
        self._user_repository = user_repository

    async def __call__(self, current_user: User, filters: dict) -> list[User]:
        if current_user.role is RoleEnum.USER:
            raise MethodNotAllowedError(current_user.id)
        if current_user.role is RoleEnum.ADMIN:
            return await self._user_repository.list(**filters)
        if current_user.role is RoleEnum.MODERATOR:
            return await self._user_repository.list_from_same_group(str(current_user.group), **filters)


class UploadImageUseCase:
    def __init__(self, images_repository: ImagesRepository, user_repository: UserRepository):
        self._images_repository = images_repository
        self._user_repository = user_repository

    async def __call__(self, current_user: User, content: bytes | None) -> str:
        s3_filename = await self._images_repository.upload_image(current_user, content)
        to_update = {'image': s3_filename}
        updated_item = replace(current_user, **to_update)
        await self._user_repository.partial_update(updated_item)
        return s3_filename



