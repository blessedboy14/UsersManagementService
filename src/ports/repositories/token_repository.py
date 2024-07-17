from abc import ABC, abstractmethod


class TokenRepository(ABC):
    @abstractmethod
    async def get(self, token: str) -> str | None:
        pass

    @abstractmethod
    async def blacklist(self, token: str) -> None:
        pass

    @abstractmethod
    async def set(self, user_id: str, token: str) -> None:
        pass

    @abstractmethod
    async def remove(self, key: str) -> None:
        pass
