from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from jose import jwt, JWTError
from sqlalchemy.exc import SQLAlchemyError

from src.users.models import User, UserPatch, RoleEnum
from src.auth.security import SECRET_KEY, ALGORITHM, oauth2_scheme
from src.users.service import (get_user,
                               update_user, delete_user,
                               get_cur_user_group, get_all_users)
from src.dependencies.core import DBSession
from src.converter.converters import convert_IN_to_DB_model

router = APIRouter()

credential_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_user(
        access_token: Annotated[str, Depends(oauth2_scheme)],
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


async def _patch_user(user_data: User, db_session: DBSession):
    try:
        await update_user(convert_IN_to_DB_model(user_data), db_session)
        await db_session.commit()
        return user_data
    except SQLAlchemyError as e:
        await db_session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    finally:
        await db_session.close()


@router.get("/me", response_model=User, summary="get current user info")
async def read_users_me(cur_user: Annotated[User, Depends(get_current_user)]):
    return cur_user


@router.patch("/me", response_model=User)
async def update_user_me(updated_user: UserPatch,
                         cur_user: Annotated[User, Depends(get_current_user)],
                         session: DBSession):
    updated_data = updated_user.model_dump(exclude_unset=True)
    updated_item = cur_user.copy(update=updated_data)
    return await _patch_user(updated_item, session)


@router.delete("/me", summary="Delete user")
async def delete_me(cur_user: Annotated[User, Depends(get_current_user)],
                    session: DBSession):
    await delete_user(cur_user.id, session)
    await session.commit()
    return {"message": "User deleted", "data": None}


@router.get("/{user_id}", summary="Get all users", response_model=list[User])
async def get_users(cur_user: Annotated[User, Depends(get_current_user)],
                    session: DBSession,
                    user_id: str):
    if cur_user.role is RoleEnum.USER:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Not allowed")
    if cur_user.role is RoleEnum.MODERATOR:
        cur_group = (await get_cur_user_group(cur_user.group_id, session))
        users_in_group = cur_group.users
        return [user for user in users_in_group if str(user.id) == user_id]

    if cur_user.role is RoleEnum.ADMIN:
        all_users = (await get_all_users(session))
        return [user for user in all_users if str(user.id) == user_id]


@router.patch("/{user_id}", response_model=User)
async def patch_user(updated_user: UserPatch, user_id: str,
                     cur_user: Annotated[User, Depends(get_current_user)],
                     session: DBSession):
    if cur_user.role is not RoleEnum.ADMIN:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Not allowed")
    to_update = await get_user(user_id, session)
    if to_update is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="User not found")
    updated_data = updated_user.model_dump(exclude_unset=True)
    patched_user = to_update.copy(update=updated_data)
    return await _patch_user(patched_user, session)


def _filter_users(users: list[User], page: int = 1, limit: int = 30,
                  filter_by_name: str = "", sort_by: str = "username", order_by: str = "desc"):
    page -= 1
    start = page * limit
    to_filter = users[start: start + limit]
    try:
        filtered = list(filter(lambda u:
                               filter_by_name.lower() in u.name.lower() or
                               filter_by_name.lower() in u.surname.lower(), to_filter))
        filtered = sorted(filtered,
                          key=lambda u: getattr(u, sort_by), reverse=True if order_by == "desc" else False
                          )
        return filtered
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid filtration params")


@router.get("/", response_model=list[User])
async def list_users(cur_user: Annotated[User, Depends(get_current_user)],
                     session: DBSession,
                     page: int = 1, limit: int = 30, filter_by_name: str = "",
                     sort_by: str = "username", order_by: str = "desc"):
    if cur_user.role is RoleEnum.USER:
        raise HTTPException(status_code=status.HTTP_405_METHOD_NOT_ALLOWED)
    if cur_user.role is RoleEnum.MODERATOR:
        moderator_group = await get_cur_user_group(cur_user.group_id, session)
        return _filter_users(moderator_group.users, page, limit, filter_by_name, sort_by,
                             order_by)
    if cur_user.role is RoleEnum.ADMIN:
        all_users = await get_all_users(session)
        return _filter_users(all_users, page, limit, filter_by_name, sort_by,
                             order_by)
