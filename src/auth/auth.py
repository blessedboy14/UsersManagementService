import json
from datetime import datetime
from typing import Annotated
import logging
from fastapi import (
    APIRouter,
    HTTPException,
    status,
    Depends,
    Form,
    UploadFile,
    File,
    Header,
)
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import EmailStr
from pydantic_extra_types.phone_numbers import PhoneNumber

from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from src.auth.models import (
    UserIn,
    AuthUser,
    LoginUser,
    TokenSchema,
    ResetPasswordRequest,
)
from src.dependencies.core import DBSession, Redis
from src.auth.service import create_user, login_user, refresh, get_by_email
from src.rabbitmq.publisher import publisher
from src.users.service import update_user
from src.users.users import upload_image

router = APIRouter()
logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s:%(levelname)s%:%(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p',
                    filename='example.log', encoding='utf-8', level=logging.DEBUG)


@router.post('/login', response_model=TokenSchema, summary='Login')
async def login(
    session: DBSession, form_data: OAuth2PasswordRequestForm = Depends()
):
    logger.info(f"login request with username: {form_data.username}")
    if form_data.username is None:
        raise HTTPException(
            status_code=401, detail='Please provide phone, email or username'
        )
    user = LoginUser(login=form_data.username, password=form_data.password)
    return await login_user(user, session)


# @router.post("/signup", status_code=status.HTTP_201_CREATED, summary="Sign Up")
# async def signup(userIn: UserIn, session: DBSession,
#                  image: UploadFile | None = None):
#     try:
#         hashed_user = await create_user(userIn, session)
#         await session.commit()
#         return AuthUser(**hashed_user.dict())
#     except IntegrityError as e:
#         await session.rollback()
#         raise HTTPException(
#             status_code=400, detail="Integrity Error(e.g. duplicate unique key)"
#         )
#     except SQLAlchemyError as e:
#         await session.rollback()
#         raise HTTPException(status_code=400, detail=str(e))
#     finally:
#         await session.close()


@router.post('/signup', status_code=status.HTTP_201_CREATED, summary='Sign Up')
async def signup(
    username: Annotated[str, Form()],
    phone: Annotated[PhoneNumber, Form()],
    email: Annotated[EmailStr, Form()],
    password: Annotated[str, Form()],
    session: DBSession,
    image: UploadFile = File(None),
):
    userIn = UserIn(email=email, phone=phone, password=password, username=username)
    logger.info(f"sign up request with data: {userIn}")
    try:
        hashed_user = await create_user(userIn, session)
        await session.commit()
        if image is not None:
            try:
                added_user = await get_by_email(email, session)
                s3_filename = await upload_image(image, session, username)
                added_user.image = s3_filename
                await update_user(added_user, session)
                await session.commit()
            except Exception as e:
                logger.error(f"sign up failed  with error: {e} ")
                raise HTTPException(
                    status_code=500, detail='Image uploading failed. {}'.format(e)
                )
        logger.info("sign up succeed")
        return AuthUser(**hashed_user.dict())
    except IntegrityError as e:
        logger.error(f"sign up failed with Integrity Error with error: {e}")
        # await session.rollback()
        raise HTTPException(
            status_code=400, detail='Integrity Error(e.g. duplicate unique key)'
        )
    except SQLAlchemyError as e:
        logger.error(f"sign up failed  with error: {e} ")
        # await session.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    # finally:
        # await session.close()


@router.post('/refresh-token', summary='Refresh Both Tokens')
async def refresh_token(redis: Redis, refresh_tkn: Annotated[str, Header()]):
    logger.info("refresh token request")
    is_valid = await refresh(refresh_tkn, redis)
    if not is_valid:
        logger.error(f"refresh token in invalid for request: {refresh_tkn}")
        raise HTTPException(status_code=401, detail='Invalid refresh token')
    return is_valid


@router.post('/reset-password', summary='Reset Your Password')
async def reset_password(request: ResetPasswordRequest, session: DBSession):
    logger.info(f"reset password request for email: {request.email}")
    is_exist = await get_by_email(request.email, session)
    if not is_exist:
        logger.info(f"requested email for reset does not exist: {request.email}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='User not found'
        )
    message = {
        'email': request.email,
        'link': 'some.url',  # TODO: create implementation
        'publish_time': json.dumps(datetime.utcnow().isoformat()),
    }
    publisher.publish_message(message)
    logger.info(f"reset password message published to rabbitmq")
    return {'message': 'message for resetting sent to rabbitmq', 'email': request.email}
