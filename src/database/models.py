import datetime
from typing import Optional, List
from sqlalchemy import DateTime, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from src.database.database import Base
from src.domain.entities.user import RoleEnum


class UserModel(Base):
    __tablename__ = 'users'

    email: Mapped[str] = mapped_column(String(60), unique=True, index=True)
    username: Mapped[str] = mapped_column(String(60), unique=True, index=True)
    phone: Mapped[str] = mapped_column(String(26), unique=True)
    name: Mapped[Optional[str]] = mapped_column(default='John')
    hashed_password: Mapped[str] = mapped_column(index=True)
    surname: Mapped[Optional[str]] = mapped_column(default='Doe')
    role: Mapped[RoleEnum] = mapped_column(default=RoleEnum.USER)
    group_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey('groups.id'), nullable=True
    )
    group: Mapped[Optional['Group']] = relationship(
        'Group', back_populates='users', lazy=False
    )
    image: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    is_blocked: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=datetime.datetime.utcnow,
    )
    modified_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=datetime.datetime.utcnow,
        onupdate=func.current_timestamp(),
    )


class Group(Base):
    __tablename__ = 'groups'

    users: Mapped[List[UserModel]] = relationship()
    name: Mapped[str]
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
