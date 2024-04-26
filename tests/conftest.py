import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import insert

from src.database.models import UserDB, Group
from src.database.database import get_session, Base
from src.main import app
from tests.utils.database_setup import get_test_session, base_user, test_session_maker
from tests.utils.fake_utils import generate_user

app.dependency_overrides[get_session] = get_test_session


@pytest_asyncio.fixture
async def async_app_client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url='https://localhost'
    ) as cli:
        yield cli


@pytest.fixture
def create_fake_user():
    return generate_user()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def async_setup_and_tear_down(request):
    async with test_session_maker.get_engine().begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(insert(Group).values({'name': 'testing', 'id': 'd9a83fd7-c45f-4c78-84eb-0922d6a5eec0'}))
        await conn.execute(insert(UserDB).values(**base_user))
    yield

    async with test_session_maker.get_engine().begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_session_maker.close()
