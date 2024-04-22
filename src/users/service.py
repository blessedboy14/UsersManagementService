import uuid
from io import BytesIO

import aioboto3
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.database.models import UserDB, Group
from src.users.models import User
from src.config.settings import settings


async def get_user(user_id: str, session: AsyncSession) -> User:
    user_db = (await session.scalars(select(UserDB).where(UserDB.id == user_id))).first()
    user = User.from_orm(user_db)
    return user


async def update_user(user: UserDB, session: AsyncSession) -> UserDB:
    await session.merge(user)
    return user


async def delete_user(user_id: uuid.UUID, session: AsyncSession):
    delete_query = delete(UserDB).where(UserDB.id == user_id)
    await session.execute(delete_query)


async def get_cur_user_group(group_id: uuid.UUID, session: AsyncSession):
    group = (await session.scalars(select(Group).where(Group.id == group_id)
                                   .options(selectinload(Group.users)))).first()
    return group


async def get_all_users(session: AsyncSession):
    users = (await session.scalars(select(UserDB).order_by(UserDB.role))).all()
    return users


async def upload_to_s3_bucket(content: BytesIO, filename: str):
    session = aioboto3.Session()
    async with session.client('s3', endpoint_url=f"http://{settings.localstack_host}:4566",
                              aws_access_key_id='test',
                              aws_secret_access_key='test',
                              ) as s3:
        try:
            await s3.upload_fileobj(content, settings.bucket_name, filename)
        except Exception as e:
            raise e
    return f"s3://{filename}"
