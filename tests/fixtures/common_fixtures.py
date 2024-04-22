import pytest_asyncio
from httpx import AsyncClient

from src.main import app


@pytest_asyncio.fixture
async def async_app_client():
    async with AsyncClient(app=app, base_url='https://localhost') as cli:
        yield cli
