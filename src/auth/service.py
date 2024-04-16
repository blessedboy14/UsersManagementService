from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import UserDB
from src.database.database import session_manager


async def create_user(user: UserDB, db_session: AsyncSession):
    async with db_session.begin():
        db_session.add(user)



