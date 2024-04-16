import uuid
import datetime
from pydantic import BaseModel
from typing import Optional
from pydantic import EmailStr
from enum import Enum


class RoleEnum(str, Enum):
    ADMIN = "admin"
    MODERATOR = "moderator"
    USER = "user"


class Group(BaseModel):

    id: uuid.UUID
    name: str
    created: datetime.date


class User(BaseModel):

    id: uuid.UUID
    name: str
    surname: str
    username: str
    hashed_password: str
    phone_number: str
    email: EmailStr
    role: RoleEnum = RoleEnum.USER
    group: Optional[Group] = None

