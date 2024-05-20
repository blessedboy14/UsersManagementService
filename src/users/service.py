import io
import uuid

import magic
from fastapi import HTTPException, UploadFile
from sqlalchemy import select, delete, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from starlette import status

from src.users.aws_s3 import upload_to_s3_bucket
from src.database.models import UserDB, Group
from src.users.exceptions import raise_upload_exception
from src.users.schemas import User, RoleEnum
from src.config.settings import MAX_FILE_SIZE, SUPPORTED_TYPES, logger
from src.utils.converters import convert_IN_to_DB_model


async def get_user(user_id: str, session: AsyncSession) -> User | None:
    logger.debug(f'getting user by id: {user_id}')
    user_db = (
        await session.scalars(select(UserDB).where(UserDB.id == user_id))
    ).first()
    if user_db is None:
        return None
    user = User.model_validate(user_db)
    return user


async def update_user(user: UserDB, session: AsyncSession) -> UserDB:
    logger.debug('updating user')
    await session.merge(user)
    return user


async def delete_user(user_id: uuid.UUID, session: AsyncSession):
    logger.debug('deleting user')
    delete_query = delete(UserDB).where(UserDB.id == user_id)
    await session.execute(delete_query)


async def get_cur_user_group(group_id: uuid.UUID, session: AsyncSession) -> Group:
    logger.debug('fetching cur user group')
    group = (
        await session.scalars(
            select(Group).where(Group.id == group_id).options(selectinload(Group.users))
        )
    ).first()
    return group


async def patch_user(user_data: User, db_session: AsyncSession) -> User:
    try:
        await update_user(convert_IN_to_DB_model(user_data), db_session)
        await db_session.commit()
        return user_data
    except SQLAlchemyError as e:
        logger.error(f'error while trying to patch user: {e}')
        await db_session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    finally:
        await db_session.close()


async def find_by_id(user_id: str, cur_user: User, session: AsyncSession) -> UserDB:
    if cur_user.role is RoleEnum.USER:
        logger.error("can't read user's as user")
        raise HTTPException(
            status_code=status.HTTP_405_METHOD_NOT_ALLOWED, detail='Not allowed'
        )
    if cur_user.role is RoleEnum.MODERATOR:
        try:
            found = list(
                await session.scalars(
                    select(UserDB).filter(
                        UserDB.id == user_id, UserDB.group_id == cur_user.group_id
                    )
                )
            )
        except SQLAlchemyError as e:
            logger.error(f'error while trying to find user: {e}')
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='User by specified id not fount',
            )
    else:
        try:
            found = list(
                await session.scalars(select(UserDB).where(UserDB.id == user_id))
            )
        except SQLAlchemyError as e:
            logger.error(f'error while trying to find user: {e}')
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='User by specified id not fount',
            )
    if not found:
        logger.error('User by specified id not found')
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='User not found'
        )
    return found[0]


async def upload_image(file: UploadFile, username: str) -> str:
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
    logger.debug('uploading image to s3')
    s3_filename = await upload_to_s3_bucket(
        io.BytesIO(file_bytes),
        f'{username}/{uuid.uuid4()}.{SUPPORTED_TYPES[file_type]}',
        username,
    )
    return s3_filename


async def fetch_filtered_users(
    user: User,
    session: AsyncSession,
    page: int = 1,
    limit: int = 30,
    filter_by_name: str = '',
    sort_by: str = 'username',
    order_by: str = 'desc',
) -> list[UserDB]:
    result_list = []
    if user.role is RoleEnum.USER:
        logger.error("can't read user's as user")
        raise HTTPException(
            status_code=status.HTTP_405_METHOD_NOT_ALLOWED, detail='Not allowed'
        )
    page = page - 1
    start = page * limit
    if sort_by not in UserDB.__dict__:
        logger.error('non-existed sort key')
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Sort key don't exist"
        )
    if user.role is RoleEnum.MODERATOR:
        result_list = await session.scalars(
            select(UserDB)
            .where(UserDB.group_id == user.group_id)
            .filter(UserDB.name.like(f'%{filter_by_name}%'))
            .offset(start)
            .limit(limit)
            .order_by(text(f'{sort_by} {order_by}'))
        )
    if user.role is RoleEnum.ADMIN:
        result_list = await session.scalars(
            select(UserDB)
            .filter(UserDB.name.like(f'%{filter_by_name}%'))
            .offset(start)
            .limit(limit)
            .order_by(text(f'{sort_by} {order_by}'))
        )
    return result_list
