import datetime
from typing import Optional
from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from src.database.database import Base
from src.users.models import RoleEnum


class UserDB(Base):
    __tablename__ = 'users'

    email: Mapped[str] = mapped_column(String(60), unique=True)
    username: Mapped[str] = mapped_column(String(60), unique=True)
    phone: Mapped[str] = mapped_column(String(15), unique=True)
    name: Mapped[Optional[str]]
    hashed_password: Mapped[str]
    surname: Mapped[Optional[str]]
    role: Mapped[RoleEnum] = relationship("Role", back_populates="users")
    group: Mapped[list["Group"]] = relationship("Group", back_populates="users")
    image: Mapped[str] = mapped_column(String(60), unique=True)
    is_blocked: Mapped[bool]
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    modified_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Role(Base):
    __tablename__ = 'roles'
    name: Mapped[RoleEnum]


class Group(Base):
    __tablename__ = 'groups'

    name: Mapped[str]
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
