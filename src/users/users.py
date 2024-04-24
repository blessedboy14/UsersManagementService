from datetime import datetime
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, Query

from src.users.models import (
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
from src.users.exceptions import raise_credential_exception

router = APIRouter()


async def get_current_user(
    access_token: Annotated[str, Depends(oauth2_scheme)], session: DBSession
):
    payload = decode_token(access_token)
    if datetime.fromtimestamp(payload['exp']) < datetime.now():
        raise_credential_exception('Token expired')
    user_id = payload.get('user_id')
    if user_id is None:
        raise_credential_exception('Token invalid')
    user = await service.get_user(user_id, session)
    if user is None:
        raise_credential_exception('Token invalid')
    return user


@router.get('/me',
            status_code=status.HTTP_200_OK,
            response_model=UserBase,
            summary='Get Yourself')
async def read_users_me(cur_user: Annotated[User, Depends(get_current_user)]):
    return cur_user


@router.patch('/me',
              status_code=status.HTTP_200_OK,
              response_model=UserBase,
              summary='Patch Yourself')
async def update_user_me(
    updated_user: UserPatch,
    cur_user: Annotated[User, Depends(get_current_user)],
    session: DBSession,
):
    updated_data = updated_user.model_dump(exclude_unset=True)
    if not updated_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='No info provided or non-existing fields',
        )
    updated_item = cur_user.copy(update=updated_data)
    return await service.patch_user(updated_item, session)


@router.delete('/me',
               status_code=status.HTTP_200_OK,
               summary='Delete Me')
async def delete_me(
    cur_user: Annotated[User, Depends(get_current_user)], session: DBSession
):
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
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail='Not allowed'
        )
    to_update = await service.get_user(user_id, session)
    if to_update is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail='User not found'
        )
    updated_data = updated_user.model_dump(exclude_unset=True)
    patched_user = to_update.copy(update=updated_data)
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
    return await service.filter_setup(
        cur_user, session, page, limit, filter_by_name, sort_by, order_by
    )


@router.post('/me/upload_image', status_code=status.HTTP_200_OK, summary='Upload Image')
async def upload_avatar_image(
    cur_user: Annotated[User, Depends(get_current_user)],
    session: DBSession,
    file: UploadFile,
):
    s3_filename = await service.upload_image(file, cur_user.username)
    to_update = {'image': s3_filename}
    updated_item = cur_user.copy(update=to_update)
    await service.patch_user(updated_item, session)
    return {'image': s3_filename, 'status': 'uploaded'}
