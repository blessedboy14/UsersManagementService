from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4


class RoleEnum(str, Enum):
    ADMIN = 'admin'
    MODERATOR = 'moderator'
    USER = 'user'


@dataclass
class User:
    email: str | None = None
    name: str | None = None
    surname: str | None = None
    username: str | None = None
    phone: str | None = None
    role: RoleEnum | None = None
    hashed_password: str | None = None
    image: str | None = None
    is_blocked: bool | None = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    modified_at: datetime = field(default_factory=datetime.utcnow)
    group: UUID | None = None
    id: UUID = field(default_factory=uuid4)


@dataclass
class LoginUser:
    login: str
    password: str


@dataclass
class UserId:
    id: UUID


@dataclass
class UserFastInfo(UserId):
    username: str
    image_url: str


@dataclass
class AuthUser:
    email: str
    password: str
    phone_number: str
    username: str
