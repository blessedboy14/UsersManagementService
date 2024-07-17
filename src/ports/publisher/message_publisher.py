from abc import ABC, abstractmethod

from src.domain.entities.reset_password_message import ResetPasswordMessage


class MessagePublisher(ABC):
    @abstractmethod
    def publish(self, message: ResetPasswordMessage):
        pass
