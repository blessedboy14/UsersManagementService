import io
import uuid
from io import BytesIO

import aioboto3
import magic
from fastapi import HTTPException, UploadFile
from sqlalchemy import select, delete
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from starlette import status

from src.database.models import UserDB, Group
from src.users.exceptions import raise_upload_exception
from src.users.models import User, RoleEnum
from src.config.settings import settings, MAX_FILE_SIZE, SUPPORTED_TYPES
from src.utils.converters import convert_IN_to_DB_model


async def get_user(user_id: str, session: AsyncSession) -> User:
    user_db = (
        await session.scalars(select(UserDB).where(UserDB.id == user_id))
    ).first()
    user = User.from_orm(user_db)
    return user


async def update_user(user: UserDB, session: AsyncSession) -> UserDB:
    await session.merge(user)
    return user


async def delete_user(user_id: uuid.UUID, session: AsyncSession):
    delete_query = delete(UserDB).where(UserDB.id == user_id)
    await session.execute(delete_query)


async def get_cur_user_group(group_id: uuid.UUID, session: AsyncSession):
    group = (
        await session.scalars(
            select(Group).where(Group.id == group_id).options(selectinload(Group.users))
        )
    ).first()
    return group


async def get_all_users(session: AsyncSession) -> list[UserDB]:
    users = list((await session.scalars(select(UserDB).order_by(UserDB.role))).all())
    return users


async def upload_to_s3_bucket(content: BytesIO, filename: str):
    session = aioboto3.Session()
    async with session.client(
        's3',
        endpoint_url=f'http://{settings.localstack_host}:4566',
        aws_access_key_id='test',
        aws_secret_access_key='test',
    ) as s3:
        try:
            await s3.upload_fileobj(content, settings.bucket_name, filename)
        except Exception as e:
            raise e
    return f's3://{filename}'


async def patch_user(user_data: User, db_session: AsyncSession):
    try:
        await update_user(convert_IN_to_DB_model(user_data), db_session)
        await db_session.commit()
        return user_data
    except SQLAlchemyError as e:
        await db_session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    finally:
        await db_session.close()


def filter_users(
    users: list[UserDB],
    page: int = 1,
    limit: int = 30,
    filter_by_name: str = '',
    sort_by: str = 'username',
    order_by: str = 'desc',
):
    page -= 1
    start = page * limit
    to_filter = users
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
        filtered = filtered[start: start + limit]
        return filtered
    except Exception:
        raise HTTPException(status_code=400, detail='Invalid filtration params')


async def filter_setup(
    cur_user: User,
    session: AsyncSession,
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
        return filter_users(
            moderator_group.users, page, limit, filter_by_name, sort_by, order_by
        )
    if cur_user.role is RoleEnum.ADMIN:
        all_users = await get_all_users(session)
        return filter_users(all_users, page, limit, filter_by_name, sort_by, order_by)


async def find_by_id(user_id: str, cur_user: User, session: AsyncSession):
    if cur_user.role is RoleEnum.USER:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail='Not allowed'
        )
    if cur_user.role is RoleEnum.MODERATOR:
        cur_group = await get_cur_user_group(cur_user.group_id, session)
        users_in_group = cur_group.users
        found = [user for user in users_in_group if str(user.id) == user_id]
        if not found:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail='User not found'
            )
        return found[0]
    if cur_user.role is RoleEnum.ADMIN:
        all_users = await get_all_users(session)
        found = [user for user in all_users if str(user.id) == user_id]
        if not found:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail='User not found'
            )
        return found[0]


async def upload_image(file: UploadFile, username: str):
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
