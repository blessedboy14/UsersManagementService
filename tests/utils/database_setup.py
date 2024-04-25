from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.database import DatabaseSessionMaker

username = 'blessedboy'
passw = 'ewkere123'
host = 'localhost:5432'
database = 'test_management_service'

string_url = f'postgresql+asyncpg://{username}:{passw}@{host}/{database}'

test_db_session = DatabaseSessionMaker(string_url, {})


existed_user = {'username': 'blessedboy', 'password': '12345678'}


async def get_test_session():
    async with test_db_session.create_session() as session:
        yield session


TestDBSession = Annotated[AsyncSession, Depends(get_test_session)]
