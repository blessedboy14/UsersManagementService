from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.users.models import User
from src.dependencies.core import DBSession
from src.auth.service import create_user
from src.database.models import UserDB
from src.converter.converters import convert_IN_to_DB_model


auth = APIRouter()


@auth.post("/login")
async def login():
    pass


@auth.post("/signup")
async def signup(user: User, session: DBSession):
    try:
        db_user = convert_IN_to_DB_model(user)
        await create_user(db_user, session)
    except SQLAlchemyError as e:
        await session.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        await session.close()
    return user


@auth.post("/reset-password")
async def signup():
    pass


@auth.post("/refresh-token")
async def signup():
    pass

