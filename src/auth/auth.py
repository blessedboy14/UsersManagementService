from fastapi import APIRouter, Depends, HTTPException, status

from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from src.auth.models import UserIn, AuthUser, LoginUser
from src.dependencies.core import DBSession
from src.auth.service import create_user, login_user


router = APIRouter()


@router.post("/login")
async def login(session: DBSession, user: LoginUser):
    if user.login is None:
        raise HTTPException(status_code=401, detail="Please provide phone, email or username")
    return await login_user(user, session)


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


@router.post("/reset-password")
async def reset_password():
    pass


@router.post("/refresh-token")
async def refresh_token():
    pass

