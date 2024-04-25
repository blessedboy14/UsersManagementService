import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from src.database.database import get_session
from src.main import app
from tests.utils.database_setup import get_test_session
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
