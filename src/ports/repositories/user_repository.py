from abc import ABC, abstractmethod
from typing import Any

from src.domain.entities.user import User, UserId, UserFastInfo


class UserRepository(ABC):
    @abstractmethod
    async def get_by_login(self, login: str) -> User | None:
        pass

    @abstractmethod
    async def get_by_email(self, email: str) -> User | None:
        pass

    @abstractmethod
    async def partial_update(self, user: User) -> User:
        pass

    @abstractmethod
    async def create(self, user: User) -> User | None:
        pass

    @abstractmethod
    async def delete(self, user_id: str) -> None:
        pass

    @abstractmethod
    async def fetch_usernames(self, user_ids: list[UserId]) -> list[UserFastInfo]:
        pass

    @abstractmethod
    async def list_from_same_group(self, group_id: str, **filters: Any) -> list[User]:
        pass

    @abstractmethod
    async def list(self, **filters: Any) -> list[User]:
        pass

    @abstractmethod
    async def get_by_id(self, user_id: str) -> User | None:
        pass
