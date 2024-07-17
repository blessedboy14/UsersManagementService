import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.database import get_session


@pytest.mark.asyncio
async def test_get_session():
    actual = await anext(get_session())
    assert isinstance(actual, AsyncSession)
