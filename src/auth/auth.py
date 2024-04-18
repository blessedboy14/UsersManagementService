import json
from datetime import datetime

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm

from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from src.auth.models import UserIn, AuthUser, LoginUser, TokenSchema, ResetPasswordRequest
from src.dependencies.core import DBSession, Redis
from src.auth.service import create_user, login_user, refresh
from src.rabbitmq.publisher import publisher


router = APIRouter()


# @router.post("/login")
# async def login(session: DBSession, user: LoginUser, redis: Redis):
#     if user.login is None:
#         raise HTTPException(status_code=401, detail="Please provide phone, email or username")
#     return await login_user(user, session, redis)


@router.post("/login", response_model=TokenSchema)
async def login(session: DBSession, redis: Redis,
                form_data: OAuth2PasswordRequestForm = Depends()):
    if form_data.username is None:
        raise HTTPException(status_code=401, detail="Please provide phone, email or username")
    user = LoginUser(login=form_data.username, password=form_data.password)
    return await login_user(user, session, redis)


@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(userIn: UserIn, session: DBSession):
    try:
        hashed_user = await create_user(userIn, session)
        await session.commit()
        return AuthUser(**hashed_user.dict())
    except IntegrityError as e:
        await session.rollback()
        raise HTTPException(status_code=400, detail="Integrity Error(e.g. duplicate unique key)")
    except SQLAlchemyError as e:
        await session.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        await session.close()


@router.post("/refresh-token")
async def refresh_token(refresh_tkn: str, redis: Redis):
    is_valid = await refresh(refresh_tkn, redis)
    if not is_valid:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    return is_valid


@router.post("/reset-password")
async def reset_password(request: ResetPasswordRequest):
    message = {"email": request.email, "link": "some.url",
               "publish_time": json.dumps(datetime.utcnow().isoformat())}
    publisher.publish_message(message)

