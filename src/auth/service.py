import json
from datetime import datetime, timedelta

from aioredis import Redis
from fastapi import HTTPException, UploadFile, File
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from src.auth.models import (
    LoginUser,
    UserIn,
    TokenSchema,
    AuthUser,
    ResetPasswordRequest,
    ResetResponseSchema,
)
from src.auth.security import (
    verify_password,
    hash_model,
    create_access_jwt,
    create_refresh_jwt,
    decode_token,
    create_link_token,
)
from src.utils.converters import convert_AUTH_to_DB
from src.database.models import UserDB
from src.users.service import update_user, upload_image
from src.rabbitmq.publisher import publisher


async def create_user(user: UserIn, db_session: AsyncSession):
    hashed_user = hash_model(user)
    db_user = convert_AUTH_to_DB(hashed_user)
    db_session.add(db_user)
    return hashed_user


async def get_by_email(email: str, db_session: AsyncSession):
    return (
        await db_session.scalars(select(UserDB).where(UserDB.email == email))
    ).first()


async def login_user(userIn: LoginUser, db_session: AsyncSession):
    db_model = await get_user(userIn, db_session)
    if db_model is not None:
        if not db_model.is_blocked:
            if verify_password(userIn.password, db_model.hashed_password):
                data = {'user_id': db_model.id.hex}
                access_token = create_access_jwt(data)
                refresh_token = create_refresh_jwt(data)
                return TokenSchema(
                    message='Logged in successfully',
                    access_token=access_token,
                    refresh_token=refresh_token,
                    type='bearer',
                )
            else:
                raise HTTPException(status_code=401, detail="Password don't match")
        else:
            raise HTTPException(status_code=401, detail='User blocked')
    else:
        raise HTTPException(status_code=401, detail='User not found')


async def get_user(userIn: LoginUser, db_session: AsyncSession) -> UserDB:
    user = (
        await db_session.scalars(
            select(UserDB).where(
                (UserDB.email == userIn.login)
                | (UserDB.phone == userIn.login)
                | (UserDB.username == userIn.login)
            )
        )
    ).first()
    return user


async def is_blacklisted(token: str, redis: Redis):
    blacklisted = await redis.get(token)
    if blacklisted:
        return True
    return False


async def refresh(token: str, redis: Redis):
    if await is_blacklisted(token, redis):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Invalid refresh token(blacklisted)',
        )
    payload = decode_token(token)
    user_id = payload.get('user_id')
    token_mode = payload.get('mode')
    if token_mode and token_mode == 'refresh_token':
        await blacklist_token(token, redis)
        data = {'user_id': user_id}
        access_token = create_access_jwt(data)
        refresh_token = create_refresh_jwt(data)
        return TokenSchema(
            message='Refresh token changed',
            access_token=access_token,
            refresh_token=refresh_token,
            type='bearer',
        )
    else:
        raise HTTPException(status_code=401, detail='Not a refresh token')


async def blacklist_token(token: str, redis: Redis):
    await redis.set(token, 'blacklisted')


async def create_new_user(
    user: UserIn,
    session: AsyncSession,
    image: UploadFile = File(None),
):
    try:
        hashed_user = await create_user(user, session)
        await session.commit()
        if image is not None:
            try:
                added_user = await get_by_email(user.email, session)
                s3_filename = await upload_image(image, user.username)
                added_user.image = s3_filename
                await update_user(added_user, session)
                await session.commit()
            except Exception as e:
                raise HTTPException(
                    status_code=500, detail='Image uploading failed. {}'.format(e)
                )
        return AuthUser(**hashed_user.model_dump())
    except IntegrityError as e:
        raise HTTPException(
            status_code=400,
            detail=f'Integrity Error(e.g. duplicate unique key); msg: {e}',
        )
    except SQLAlchemyError as e:
        raise HTTPException(status_code=400, detail=str(e))


def _generate_reset_password_url(email: str):
    payload = {
        'email': email,
        'type': 'reset_password',
        'expiry': (datetime.utcnow() + timedelta(days=30)).isoformat(),
    }
    token = create_link_token(payload)
    reset_link = 'https://127.0.0.1:8000/auth/password/reset?token=' + token
    return reset_link


async def send_reset_password_message(
    request: ResetPasswordRequest, db_session: AsyncSession
):
    is_exist = await get_by_email(request.email, db_session)
    if not is_exist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='User not found'
        )
    message = {
        'email': request.email,
        'link': _generate_reset_password_url(request.email),
        'publish_time': json.dumps(datetime.utcnow().isoformat()),
    }
    publisher.publish_message(message)
    return ResetResponseSchema(
        message='message for resetting sent to rabbitmq', email=request.email
    )
