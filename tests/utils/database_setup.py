from src.config.settings import settings
from src.database.database import DatabaseSessionMaker
from src.drivers.rest.routers.schema import RoleEnum
from src.common.security import get_password_hash

username = settings.username
passw = settings.passw
host = f'{settings.test_postgres_host}:{settings.test_db_port}'
database = settings.test_db

string_url = f'postgresql+asyncpg://{username}:{passw}@{host}/{database}'

test_session_maker = DatabaseSessionMaker(string_url, {})
base_user = {
    'username': username,
    'hashed_password': get_password_hash('12345678'),
    'phone': '+375291235678',
    'email': 'ewkere@email.com',
    'role': RoleEnum.ADMIN,
}

existed_user = {'username': username, 'password': '12345678'}


async def get_test_session():
    async with test_session_maker.create_session() as session:
        yield session
