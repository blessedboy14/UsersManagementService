from abc import ABC, abstractmethod

from src.domain.entities.user import User


class ImagesRepository(ABC):
    @abstractmethod
    async def upload_image(self, current_user: User, content: bytes | None) -> str:
        pass
