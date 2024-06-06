from datetime import datetime
from uuid import UUID
from dataclasses import dataclass, field


@dataclass
class ResetPasswordMessage:
    user_id: str
    subject: str
    body: str
    email: str
    published_at: str


@dataclass
class ResetPasswordResponse:
    message: str
    email: str
