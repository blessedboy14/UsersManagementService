from typing import Any

from sqlalchemy import select, delete, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.exceptions import DatabaseError, InvalidIdError, NonExistSortKeyError
from src.database.models import UserModel
from src.domain.entities.user import User
from src.ports.repositories.user_repository import UserRepository
from src.adapters.config import logger


class PostgreUserRepository(UserRepository):
    async def get_by_login(self, login: str) -> User | None:
        user = (
            await self._session.scalars(
                select(UserModel).where(
                    (UserModel.email == login)
                    | (UserModel.phone == login)
                    | (UserModel.username == login)
                )
            )
        ).first()
        return None if not user else self._to_dataclass(user)

    async def get_by_email(self, email: str) -> User | None:
        user = (
            await self._session.scalars(
                select(UserModel).where(UserModel.email == email)
            )
        ).first()
        return None if not user else self._to_dataclass(user)

    async def partial_update(self, user: User) -> User:
        user_model = UserModel(**user.__dict__)
        try:
            await self._session.merge(user_model)
            await self._session.commit()
        except Exception as e:
            logger.error(f'Partial update failed with error: {e}')
            await self._session.rollback()
            raise DatabaseError(e)
        return user

    async def create(self, user: User) -> User | None:
        try:
            self._session.add(UserModel(**user.__dict__))
            await self._session.commit()
            _ = (
                await self._session.execute(
                    select(UserModel).where(UserModel.username == user.username)
                )
            ).first()
            return user
        except Exception as e:
            logger.error(f'User creating failed with error: {e}')
            await self._session.rollback()
            raise DatabaseError(e)

    async def delete(self, user_id: str) -> None:
        try:
            await self._session.execute(
                delete(UserModel).where(UserModel.id == user_id)
            )
            await self._session.commit()
        except Exception as e:
            logger.error(e)
            await self._session.rollback()
            raise DatabaseError(e)

    async def list_from_same_group(self, group_id: str, **filters: Any) -> list[User]:
        filter_by_name = filters['filter_by_name']
        limit = filters.get('limit', 30)
        start = (filters.get('page', 0) - 1) * limit
        sort_by = filters.get('sort_by', 'username')
        order_by = filters.get('order_by', 'desc')
        query = (
            select(UserModel)
            .where(UserModel.group == group_id)
            .filter(UserModel.name.like(f'%{filter_by_name}%'))
            .offset(start)
            .limit(limit)
            .order_by(text(f'{sort_by} {order_by}'))
        )
        try:
            result_list = await self._session.scalars(query)
        except Exception as e:
            logger.error(
                f'Users listing failed probably due to non-exist sort key: {e}'
            )
            raise NonExistSortKeyError(sort_by)
        return [self._to_dataclass(user) for user in result_list]

    async def list(self, **filters: dict) -> list[User]:
        filter_by_name = filters['filter_by_name']
        limit = filters.get('limit', 30)
        start = (filters.get('page', 0) - 1) * limit
        sort_by = filters.get('sort_by', 'username')
        order_by = filters.get('order_by', 'desc')
        query = (
            select(UserModel)
            .filter(UserModel.name.like(f'%{filter_by_name}%'))
            .offset(start)
            .limit(limit)
            .order_by(text(f'{sort_by} {order_by}'))
        )
        try:
            result_list = await self._session.scalars(query)
        except Exception as e:
            logger.error(
                f'Users listing failed probably due to non-exist sort key: {e}'
            )
            raise NonExistSortKeyError(sort_by)
        return [self._to_dataclass(user) for user in result_list]

    async def get_by_id(self, user_id: str) -> User | None:
        try:
            user_model = (
                await self._session.scalars(
                    select(UserModel).where(UserModel.id == user_id)
                )
            ).first()
        except Exception as e:
            logger.error(f'Fetching by id failed with error: {e}')
            raise InvalidIdError(user_id)
        return None if not user_model else self._to_dataclass(user_model)

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def _to_dataclass(model: UserModel) -> User:
        return User(
            email=model.email,
            phone=model.phone,
            username=model.username,
            role=model.role,
            group=model.group,
            image=model.image,
            is_blocked=model.is_blocked,
            id=model.id,
            name=model.name,
            surname=model.surname,
            created_at=model.created_at,
            modified_at=model.modified_at,
            hashed_password=model.hashed_password,
        )
