from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import LoginUser, UserIn
from src.auth.security import verify_password, hash_model
from src.converter.converters import convert_AUTH_to_DB
from src.database.models import UserDB
from src.database.database import session_manager


def create_user(user: UserIn, db_session: AsyncSession):
    hashed_user = hash_model(user)
    db_user = convert_AUTH_to_DB(hashed_user)
    db_session.add(db_user)
    return hashed_user


def _verify_field_matching(db_model: UserDB, user: LoginUser) -> bool:
    return (db_model.username == user.username
            and db_model.email == user.email
            and db_model.phone == user.phone)


async def login_user(userIn: LoginUser, db_session: AsyncSession):
    db_model = (await get_user(userIn, db_session))
    if db_model is not None:
        if verify_password(userIn.password, db_model.hashed_password):
            return {"access_token": db_model.id, "refresh_token": db_model.username}
        else:
            raise HTTPException(status_code=400, detail="Incorrect password")
    else:
        raise HTTPException(status_code=400, detail="User not found")


async def get_user(userIn: LoginUser, db_session: AsyncSession) -> UserDB:
    user = ((await db_session.scalars(select(UserDB)
                                      .where((UserDB.email == userIn.login)
                                             | (UserDB.phone == userIn.login)
                                             | (UserDB.username == userIn.login))))
            .first())
    return user
