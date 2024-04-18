import uuid

from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.database.models import UserDB, Group
from src.users.models import User


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
