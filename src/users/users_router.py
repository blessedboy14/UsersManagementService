from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from jose import jwt, JWTError
from sqlalchemy.exc import SQLAlchemyError

from src.users.models import User
from src.auth.security import SECRET_KEY, ALGORITHM
from src.users.service import get_user, update_user
from src.dependencies.core import DBSession
from src.converter.converters import convert_IN_to_DB_model

router = APIRouter()

credential_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_user(
        access_token: str,
        session: DBSession):
    try:
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get('user_id')
        if user_id is None:
            raise credential_exception
    except JWTError:
        raise credential_exception
    user = await get_user(user_id, session)
    if user is None:
        raise credential_exception
    return user


@router.get("/me", response_model=User)
async def read_users_me(cur_user: Annotated[User, Depends(get_current_user)]):
    return cur_user


@router.patch("/me", response_model=User)
async def update_user_me(updated_user: User,
                         cur_user: Annotated[User, Depends(get_current_user)],
                         session: DBSession):
    updated_data = updated_user.model_dump(exclude_unset=True)
    updated_item = cur_user.copy(update=updated_data)
    try:
        user = await update_user(convert_IN_to_DB_model(updated_item), session)
        await session.commit()
        return user
    except SQLAlchemyError:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="DB error")
    finally:
        await session.close()
