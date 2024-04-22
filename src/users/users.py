import io
import uuid
from datetime import datetime
from typing import Annotated
import magic
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile
from jose import jwt, JWTError
from sqlalchemy.exc import SQLAlchemyError

from src.users.models import User, UserPatch, RoleEnum, UserBase, AdminPatch
from src.auth.security import SECRET_KEY, ALGORITHM, oauth2_scheme
from src.users.service import (
    get_user,
    upload_to_s3_bucket,
    update_user,
    delete_user,
    get_cur_user_group,
    get_all_users,
)
from src.dependencies.core import DBSession
from src.config.settings import MAX_FILE_SIZE, SUPPORTED_TYPES
from src.converter.converters import convert_IN_to_DB_model

router = APIRouter()


def raise_credential_exception(message: str):
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=message,
        headers={'WWW-Authenticate': 'Bearer'},
    )


async def get_current_user(
    access_token: Annotated[str, Depends(oauth2_scheme)], session: DBSession
):
    user_id = None
    try:
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        if datetime.fromtimestamp(payload['exp']) < datetime.now():
            raise_credential_exception('Token expired')
        user_id = payload.get('user_id')
        if user_id is None:
            raise_credential_exception('Token invalid')
    except JWTError:
        raise_credential_exception('Token invalid')
    user = await get_user(user_id, session)
    if user is None:
        raise_credential_exception('Token invalid')
    return user


async def _patch_user(user_data: User, db_session: DBSession):
    try:
        await update_user(convert_IN_to_DB_model(user_data), db_session)
        await db_session.commit()
        return user_data
    except SQLAlchemyError as e:
        await db_session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    finally:
        await db_session.close()


@router.get('/me', response_model=UserBase, summary='Get Yourself')
async def read_users_me(cur_user: Annotated[User, Depends(get_current_user)]):
    return cur_user


@router.patch('/me', response_model=UserBase, summary='Patch Yourself')
async def update_user_me(
    updated_user: UserPatch,
    cur_user: Annotated[User, Depends(get_current_user)],
    session: DBSession,
):
    updated_data = updated_user.model_dump(exclude_unset=True)
    updated_item = cur_user.copy(update=updated_data)
    return await _patch_user(updated_item, session)


@router.delete('/me', summary='Delete Me')
async def delete_me(
    cur_user: Annotated[User, Depends(get_current_user)], session: DBSession
):
    await delete_user(cur_user.id, session)
    await session.commit()
    return {'message': 'User deleted', 'data': None}


@router.get('/{user_id}', summary='Get User By Id', response_model=list[UserBase])
async def get_users(
    cur_user: Annotated[User, Depends(get_current_user)],
    session: DBSession,
    user_id: str,
):
    if cur_user.role is RoleEnum.USER:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail='Not allowed'
        )
    if cur_user.role is RoleEnum.MODERATOR:
        cur_group = await get_cur_user_group(cur_user.group_id, session)
        users_in_group = cur_group.users
        return [user for user in users_in_group if str(user.id) == user_id]

    if cur_user.role is RoleEnum.ADMIN:
        all_users = await get_all_users(session)
        return [user for user in all_users if str(user.id) == user_id]


@router.patch('/{user_id}', response_model=UserBase, summary='Patch User As Admin')
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
    to_update = await get_user(user_id, session)
    if to_update is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail='User not found'
        )
    updated_data = updated_user.model_dump(exclude_unset=True)
    patched_user = to_update.copy(update=updated_data)
    return await _patch_user(patched_user, session)


def _filter_users(
    users: list[User],
    page: int = 1,
    limit: int = 30,
    filter_by_name: str = '',
    sort_by: str = 'username',
    order_by: str = 'desc',
):
    page -= 1
    start = page * limit
    to_filter = users[start : start + limit]
    try:
        filtered = list(
            filter(
                lambda u: filter_by_name.lower() in u.name.lower()
                or filter_by_name.lower() in u.surname.lower(),
                to_filter,
            )
        )
        filtered = sorted(
            filtered,
            key=lambda u: getattr(u, sort_by),
            reverse=True if order_by == 'desc' else False,
        )
        return filtered
    except Exception:
        raise HTTPException(status_code=400, detail='Invalid filtration params')


@router.get('', response_model=list[UserBase], summary='List Users')
async def list_users(
    cur_user: Annotated[User, Depends(get_current_user)],
    session: DBSession,
    page: int = 1,
    limit: int = 30,
    filter_by_name: str = '',
    sort_by: str = 'username',
    order_by: str = 'desc',
):
    if cur_user.role is RoleEnum.USER:
        raise HTTPException(status_code=status.HTTP_405_METHOD_NOT_ALLOWED)
    if cur_user.role is RoleEnum.MODERATOR:
        moderator_group = await get_cur_user_group(cur_user.group_id, session)
        return _filter_users(
            moderator_group.users, page, limit, filter_by_name, sort_by, order_by
        )
    if cur_user.role is RoleEnum.ADMIN:
        all_users = await get_all_users(session)
        return _filter_users(all_users, page, limit, filter_by_name, sort_by, order_by)


def raise_upload_exception(msg: str):
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)


@router.post('/me/upload_image', summary='Upload Image')
async def upload_avatar_image(
    cur_user: Annotated[User, Depends(get_current_user)],
    session: DBSession,
    file: UploadFile,
):
    s3_filename = await upload_image(file, session, cur_user.username)
    to_update = {'image': s3_filename}
    updated_item = cur_user.copy(update=to_update)
    await _patch_user(updated_item, session)
    return {'image': s3_filename, 'status': 'uploaded'}


async def upload_image(file: UploadFile, db_session: DBSession, username: str):
    if not file:
        raise_upload_exception('File not presented')

    file_bytes = await file.read()
    file_size = len(file_bytes)
    if file_size < 1 or file_size > MAX_FILE_SIZE:
        raise_upload_exception('File size is too big')

    file_type = magic.from_buffer(file_bytes, mime=True)
    if file_type not in SUPPORTED_TYPES:
        raise_upload_exception(
            f'Unsupported file type {file_type}. Supported types: {SUPPORTED_TYPES}'
        )
    s3_filename = await upload_to_s3_bucket(
        io.BytesIO(file_bytes),
        f'{username}/{uuid.uuid4()}.{SUPPORTED_TYPES[file_type]}',
    )
    return s3_filename
