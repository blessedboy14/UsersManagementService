from typing import Annotated, AsyncIterator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from aioredis import from_url, Redis
from src.database.database import get_session
from src.config.settings import settings


DBSession = Annotated[AsyncSession, Depends(get_session)]


async def init_redis_pool() -> AsyncIterator[Redis]:
    redis_session = from_url(f"redis://{settings.redis_host}", password=settings.passw, encoding="utf-8", decode_responses=True)
    yield redis_session
    await redis_session.close()


Redis = Annotated[Redis, Depends(init_redis_pool)]
