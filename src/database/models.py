import datetime
from typing import Optional, List
from sqlalchemy import DateTime, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from src.database.database import Base
from src.users.models import RoleEnum


class UserDB(Base):
    __tablename__ = 'users'

    email: Mapped[str] = mapped_column(String(60), unique=True)
    username: Mapped[str] = mapped_column(String(60), unique=True)
    phone: Mapped[str] = mapped_column(String(26), unique=True)
    name: Mapped[Optional[str]] = mapped_column(default='John')
    hashed_password: Mapped[str]
    surname: Mapped[Optional[str]] = mapped_column(default='Doe')
    role: Mapped[RoleEnum] = mapped_column(default=RoleEnum.USER)
    group_id: Mapped[str] = mapped_column(
        ForeignKey('groups.id'), default='d9a83fd7-c45f-4c78-84eb-0922d6a5eec0'
    )
    group: Mapped['Group'] = relationship('Group', back_populates='users', lazy=False)
    image: Mapped[str] = mapped_column(String(64), default='/static/img/user.png')
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

    users: Mapped[List[UserDB]] = relationship()
    name: Mapped[str]
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
