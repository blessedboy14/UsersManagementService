import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, status, UploadFile, Query

from src.auth.exceptions import NotFoundException
from src.users.schemas import (
    User,
    UserPatch,
    RoleEnum,
    UserBase,
    AdminPatch,
    OrderByEnum,
)
from src.auth.security import oauth2_scheme, decode_token
import src.users.service as service
from src.dependencies.core import DBSession
from src.users.exceptions import (
    CredentialException,
    EmptyInputDataException,
    NotAllowedException,
)
from src.config.settings import logger

router = APIRouter()


async def get_current_user(
    access_token: Annotated[str, Depends(oauth2_scheme)], session: DBSession
) -> User:
    payload = decode_token(access_token)
    user_id = payload.get('user_id')
    if user_id is None:
        raise CredentialException('Token invalid')
    user = await service.get_user(user_id, session)
    if user is None:
        raise CredentialException("User don't exist")
    return user


@router.get(
    '/me',
    status_code=status.HTTP_200_OK,
    response_model=UserBase,
    summary='Get Yourself',
)
async def read_users_me(cur_user: Annotated[User, Depends(get_current_user)]):
    logger.info('reading current user')
    return cur_user


@router.patch(
    '/me',
    status_code=status.HTTP_200_OK,
    response_model=UserBase,
    summary='Patch Yourself',
)
async def update_user_me(
    updated_user: UserPatch,
    cur_user: Annotated[User, Depends(get_current_user)],
    session: DBSession,
):
    logger.info(
        f'updating current user "{cur_user.username}" with data {updated_user.model_dump(exclude_none=True)}'
    )
    updated_data = updated_user.model_dump(exclude_unset=True)
    if not updated_data:
        logger.error(
            f'update request provide no data that can be updated, maybe non-exist field, data: {updated_data}'
        )
        raise EmptyInputDataException(
            message='No info provided or non-existing fields',
        )
    updated_item = cur_user.model_copy(update=updated_data)
    return await service.patch_user(updated_item, session)


@router.delete('/me', status_code=status.HTTP_200_OK, summary='Delete Me')
async def delete_me(
    cur_user: Annotated[User, Depends(get_current_user)], session: DBSession
):
    logger.info(f'performing delete of user "{cur_user.username}"')
    await service.delete_user(cur_user.id, session)
    await session.commit()
    return {'message': 'User deleted', 'data': None}


@router.get(
    '/{user_id}',
    status_code=status.HTTP_200_OK,
    response_model=UserBase,
    summary='Get User By Id',
)
async def get_users(
    cur_user: Annotated[User, Depends(get_current_user)],
    session: DBSession,
    user_id: str,
):
    return await service.find_by_id(user_id, cur_user, session)


@router.patch(
    '/{user_id}',
    status_code=status.HTTP_200_OK,
    response_model=UserBase,
    summary='Patch User As Admin',
)
async def patch_user(
    updated_user: AdminPatch,
    user_id: str,
    cur_user: Annotated[User, Depends(get_current_user)],
    session: DBSession,
):
    if cur_user.role is not RoleEnum.ADMIN:
        logger.error(
            f"attempt to patch user by id, when current user isn't admin: {cur_user.username}"
        )
        raise NotAllowedException(
            reason='Not allowed',
            role=cur_user.role,
        )
    to_update = await service.get_user(user_id, session)
    if to_update is None:
        logger.error(
            f'attempt by admin to patch non-exist user, admin: {cur_user.username}'
        )
        raise NotFoundException(message='User not found')
    updated_data = updated_user.model_dump(exclude_unset=True)
    if not updated_data:
        logger.error(
            f'attempt by admin to patch user, but provide no correct data: {updated_data}'
        )
        raise EmptyInputDataException(
            message='No info provided or non-existing fields',
        )
    patched_user = to_update.model_copy(update=updated_data)
    return await service.patch_user(patched_user, session)


@router.get(
    '',
    status_code=status.HTTP_200_OK,
    response_model=list[UserBase],
    summary='List Users',
)
async def list_users(
    cur_user: Annotated[User, Depends(get_current_user)],
    session: DBSession,
    page: Annotated[int, Query(gt=0)] = 1,
    limit: Annotated[int, Query(gt=-1, lt=101)] = 30,
    filter_by_name: str = '',
    sort_by: str = 'username',
    order_by: OrderByEnum = OrderByEnum.DESC,
):
    return await service.fetch_filtered_users(
        cur_user, session, page, limit, filter_by_name, sort_by, order_by
    )


@router.post('/me/upload_image', status_code=status.HTTP_200_OK, summary='Upload Image')
async def upload_avatar_image(
    cur_user: Annotated[User, Depends(get_current_user)],
    session: DBSession,
    file: UploadFile,
):
    logger.info(f'upload image to s3 localstack request from "{cur_user.username}"')
    s3_filename = await service.upload_image(file, cur_user.username)
    to_update = {'image': s3_filename}
    updated_item = cur_user.model_copy(update=to_update)
    await service.patch_user(updated_item, session)
    return {'image': s3_filename, 'status': 'uploaded'}


@router.delete('/{user_id}', status_code=status.HTTP_200_OK, summary='Delete User')
async def delete_user_as_admin(
    cur_user: Annotated[User, Depends(get_current_user)],
    user_id: str,
    session: DBSession,
):
    if cur_user.role is not RoleEnum.ADMIN:
        logger.info(
            f'attempt to delete user by id from non-admin user: {cur_user.username}'
        )
        raise NotAllowedException(
            reason='Not allowed',
            role=cur_user.role,
        )
    await service.delete_user(uuid.UUID(user_id), session)
    await session.commit()
    return {'message': f'user with id {user_id} deleted'}
