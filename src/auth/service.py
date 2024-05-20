from datetime import datetime, timedelta

from aioredis import Redis
from fastapi import UploadFile, File
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from src.auth.schemas import (
    LoginUser,
    UserIn,
    TokenSchema,
    AuthUser,
    ResetPasswordRequest,
    ResetPasswordMessage,
    UserInDB,
    ResetPasswordResponse,
)
from src.auth.security import (
    verify_password,
    hash_model,
    create_access_jwt,
    create_refresh_jwt,
    decode_token,
    create_link_token,
)
from src.auth.exceptions import (
    LoginUserException,
    RefreshTokenException,
    CreateUserException,
    NotFoundException,
)
from src.utils.converters import convert_AUTH_to_DB
from src.config.settings import logger
from src.database.models import UserDB
from src.users.service import update_user, upload_image
from src.rabbitmq.publisher import publisher


async def create_user(user: UserIn, db_session: AsyncSession) -> UserInDB:
    hashed_user = hash_model(user)
    hashed_database_model = convert_AUTH_to_DB(hashed_user)
    db_session.add(hashed_database_model)
    logger.info(f'user "{user.username}" created')
    return hashed_user


async def get_by_email(email: str, db_session: AsyncSession) -> UserDB:
    return (
        await db_session.scalars(select(UserDB).where(UserDB.email == email))
    ).first()


async def login_user(userIn: LoginUser, db_session: AsyncSession) -> TokenSchema:
    user = await get_user(userIn, db_session)
    if user is not None:
        if not user.is_blocked:
            if verify_password(userIn.password, user.hashed_password):
                data = {'user_id': user.id.hex}
                refresh_token = create_refresh_jwt(data)
                data.update({'group_id': str(user.group_id)})
                access_token = create_access_jwt(data)
                logger.info(f'user "{userIn.login}" logged in')
                return TokenSchema(
                    message='Logged in successfully',
                    access_token=access_token,
                    refresh_token=refresh_token,
                    type='bearer',
                )
            else:
                logger.error("User password don't match with existed")
                raise LoginUserException(
                    reason="Password don't match", username=user.username
                )
        else:
            logger.error(f'User is blocked: {userIn.login}')
            raise LoginUserException(username=user.username, reason='User blocked')
    else:
        logger.error(f'User not found in the database: {userIn.login}')
        raise LoginUserException(username=userIn.login, reason='User not found')


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


async def is_blacklisted(token: str, redis: Redis) -> bool:
    blacklisted = await redis.get(token)
    logger.debug('Checking token blacklist status')
    if blacklisted:
        return True
    return False


async def refresh(token: str, redis: Redis) -> TokenSchema:
    if await is_blacklisted(token, redis):
        logger.error('Token is defined as blacklisted')
        raise RefreshTokenException(
            exc_status=status.HTTP_400_BAD_REQUEST,
            reason='Invalid refresh token(blacklisted)',
            token=token,
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
        logger.error("provided token isn't refresh token(invalid payload)")
        raise RefreshTokenException(
            exc_status=401, reason='Not a refresh token', token=token
        )


async def blacklist_token(token: str, redis: Redis):
    logger.debug('Attempt to blacklist token with redis')
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
            added_user = await get_by_email(user.email, session)
            logger.info(
                f'user "{user.username}" created with image, trying to upload image'
            )
            s3_filename = await upload_image(image, user.username)
            added_user.image = s3_filename
            await update_user(added_user, session)
            await session.commit()
            logger.info(f'image uploaded for user "{user.username}"')
        logger.debug(f'user "{user.username}" created without image')
        return AuthUser(**hashed_user.model_dump())
    except IntegrityError as e:
        logger.error(f'integrity error, unique already exists: {e}')
        raise CreateUserException(
            username=user.username,
            reason=f'Integrity Error; msg: {e}',
        )


def _generate_reset_password_url(email: str, user_id: str):
    payload = {
        'email': email,
        'type': 'reset_password',
        'expiry': (datetime.utcnow() + timedelta(days=30)).isoformat(),
    }
    logger.debug(f'generating reset password link for: {email}')
    token = create_link_token(payload)
    reset_link = f'https://127.0.0.1:8000/auth/reset-password/{user_id}?token=' + token
    return reset_link


async def send_reset_password_message(
    request: ResetPasswordRequest, db_session: AsyncSession
):
    is_exist = await get_by_email(request.email, db_session)
    if not is_exist:
        logger.error(f"user with email {request.email} don't exist")
        raise NotFoundException(message='User not found')
    message = ResetPasswordMessage(
        user_id=is_exist.id,
        subject=f'Resetting Password To Your Account: {request.email}',
        body='Click this link to reset your password '
        f'{_generate_reset_password_url(request.email, str(is_exist.id))}',
        email=request.email,
        published_at=datetime.utcnow(),
    )
    to_send = message.model_dump().copy()
    to_send.update(
        {
            'user_id': str(to_send['user_id']),
            'published_at': to_send['published_at'].isoformat(),
        }
    )
    logger.debug('sending message to rabbitmq queue')
    publisher.publish_message(to_send)
    return ResetPasswordResponse(
        message='Reset link was sent to your email', email=request.email
    )
