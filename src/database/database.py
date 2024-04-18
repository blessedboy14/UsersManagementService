import uuid
import contextlib
from typing import Any, AsyncIterator
from src.config.settings import string_url
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncConnection,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class DatabaseSessionMaker:
    def __init__(self, urlPath: str, kwargs: dict[str, Any]):
        self._engine = create_async_engine(urlPath, **kwargs)
        self._sessionmaker = async_sessionmaker(bind=self._engine, expire_on_commit=False)

    async def close(self):
        if self._engine is None:
            raise Exception("DatabaseSessionMaker: engine is None")
        await self._engine.dispose()

        self._sessionmaker = None
        self._engine = None

    @contextlib.asynccontextmanager
    async def create_session(self) -> AsyncIterator[AsyncSession]:
        if self._sessionmaker is None:
            raise Exception("DatabaseSessionMaker: sessionmaker is None")

        session = self._sessionmaker()
        try:
            yield session
        except Exception as e:
            await session.rollback()
            raise e
        finally:
            await session.close()

    @contextlib.asynccontextmanager
    async def create_connection(self) -> AsyncIterator[AsyncConnection]:
        if self._engine is None:
            raise Exception("DatabaseSessionMaker: engine is None")

        async with self._engine.begin() as conn:
            try:
                yield conn
            except Exception as e:
                await conn.rollback()
                raise e

    def get_engine(self):
        return self._engine


session_manager = DatabaseSessionMaker(string_url, {})


async def get_session():
    async with session_manager.create_session() as session:
        yield session


class Base(DeclarativeBase):
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
