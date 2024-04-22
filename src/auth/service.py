from aioredis import Redis
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import LoginUser, UserIn, TokenSchema
from src.auth.security import (
    verify_password, hash_model, create_access_jwt, create_refresh_jwt,
    decode_token
)
from src.converter.converters import convert_AUTH_to_DB
from src.database.models import UserDB


async def create_user(user: UserIn, db_session: AsyncSession):
    hashed_user = hash_model(user)
    db_user = convert_AUTH_to_DB(hashed_user)
    async with db_session.begin():
        db_session.add(db_user)
    return hashed_user


async def login_user(userIn: LoginUser, db_session: AsyncSession, redis: Redis):
    db_model = (await get_user(userIn, db_session))
    if db_model is not None:
        if verify_password(userIn.password, db_model.hashed_password):
            # create jwt access token
            data = {'user_id': db_model.id.hex}
            access_token = create_access_jwt(data)
            # create refresh token
            refresh_token = create_refresh_jwt(data)
            await redis.set(refresh_token, db_model.id.hex)
            return TokenSchema(
                message='Logged in successfully',
                access_token=access_token,
                refresh_token=refresh_token,
                type="bearer"
            )
        else:
            raise HTTPException(status_code=401, detail="Password don't match")
    else:
        raise HTTPException(status_code=401, detail="User not found")


async def get_user(userIn: LoginUser, db_session: AsyncSession) -> UserDB:
    user = ((await db_session.scalars(select(UserDB)
                                      .where((UserDB.email == userIn.login)
                                             | (UserDB.phone == userIn.login)
                                             | (UserDB.username == userIn.login))))
            .first())
    return user


async def refresh(token: str, redis: Redis):
    payload = await decode_token(token)
    user_id = payload.get('user_id')
    id_from_db = await redis.get(token)
    if id_from_db != user_id or id_from_db == "blacklisted":
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    await blacklist_token(token, redis)
    data = {'user_id': user_id}
    access_token = create_access_jwt(data)
    # create refresh token
    refresh_token = create_refresh_jwt(data)
    await redis.set(refresh_token, user_id)
    return TokenSchema(
        message='Refresh token changed',
        access_token=access_token,
        refresh_token=refresh_token,
        type="bearer"
    )


async def blacklist_token(token: str, redis: Redis):
    await redis.set(token, "blacklisted")

