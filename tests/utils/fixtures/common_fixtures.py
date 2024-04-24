import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from src.database.database import get_session
from src.main import app
from tests.utils.database.setup import get_test_session

app.dependency_overrides[get_session] = get_test_session


@pytest_asyncio.fixture
async def async_app_client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url='https://localhost'
    ) as cli:
        yield cli
