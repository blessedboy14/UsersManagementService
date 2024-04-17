from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import UserDB
from src.users.models import User


async def get_user(user_id: str, session: AsyncSession) -> UserDB:
    user = (await session.scalars(select(UserDB).where(UserDB.id == user_id))).first()
    return user


async def update_user(user: UserDB, session: AsyncSession) -> UserDB:
    async with session.begin():
        session.add(user)
    return user
