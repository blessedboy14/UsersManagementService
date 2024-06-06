from typing import Annotated
from fastapi import APIRouter, Depends, status, UploadFile, Query

from src.domain.entities.user import User
from src.drivers.rest.dependencies import (
    get_patch_me_use_case,
    get_delete_me_use_case,
    get_get_user_by_id_use_case,
    get_patch_user_by_id_use_case,
    get_list_users_use_case,
    get_upload_file_use_case,
    get_delete_by_id_use_case,
    get_auth_with_jwt_use_case,
)
from src.use_cases.auth_use_cases import AuthUserWithJWTUseCase
from src.use_cases.users_use_cases import (
    PatchMeUseCase,
    DeleteMeUseCase,
    GetUserByIdUseCase,
    PatchUserByIdUseCase,
    ListUsersUseCase,
    UploadImageUseCase,
    DeleteUserByIdUseCase,
)
from src.drivers.rest.routers.schema import (
    UserPatch,
    UserBase,
    AdminPatch,
    OrderByEnum,
)
from src.common.security import oauth2_scheme

router = APIRouter()


async def get_current_user(
    access_token: Annotated[str, Depends(oauth2_scheme)],
    use_case: Annotated[AuthUserWithJWTUseCase, Depends(get_auth_with_jwt_use_case)],
) -> User:
    return await use_case(access_token)


@router.get(
    '/me',
    status_code=status.HTTP_200_OK,
    response_model=UserBase,
    summary='Get Yourself',
)
async def read_users_me(cur_user: Annotated[User, Depends(get_current_user)]):
    return cur_user


@router.patch(
    '/me',
    status_code=status.HTTP_200_OK,
    response_model=UserBase,
    summary='Patch Yourself',
)
async def update_user_me(
    updated_user: UserPatch,
    cur_user: Annotated[User, Depends(get_current_user)],
    use_case: Annotated[PatchMeUseCase, Depends(get_patch_me_use_case)],
):
    updated_dict = updated_user.model_dump(exclude_unset=True)
    return await use_case(updated_dict, cur_user)


@router.delete('/me', status_code=status.HTTP_200_OK, summary='Delete Me')
async def delete_me(
    cur_user: Annotated[User, Depends(get_current_user)],
    use_case: Annotated[DeleteMeUseCase, Depends(get_delete_me_use_case)],
):
    await use_case(cur_user)


@router.get(
    '/{user_id}',
    status_code=status.HTTP_200_OK,
    response_model=UserBase,
    summary='Get User By Id',
)
async def get_user_by_id(
    cur_user: Annotated[User, Depends(get_current_user)],
    use_case: Annotated[GetUserByIdUseCase, Depends(get_get_user_by_id_use_case)],
    user_id: str,
):
    return await use_case(cur_user, user_id)


@router.patch(
    '/{user_id}',
    status_code=status.HTTP_200_OK,
    response_model=UserBase,
    summary='Patch User As Admin',
)
async def patch_user(
    updated_user: AdminPatch,
    user_id: str,
    cur_user: Annotated[User, Depends(get_current_user)],
    use_case: Annotated[PatchUserByIdUseCase, Depends(get_patch_user_by_id_use_case)],
):
    updated_dict = updated_user.model_dump(exclude_unset=True)
    return await use_case(cur_user, user_id, updated_dict)


@router.get(
    '',
    status_code=status.HTTP_200_OK,
    response_model=list[UserBase],
    summary='List Users',
)
async def list_users(
    cur_user: Annotated[User, Depends(get_current_user)],
    use_case: Annotated[ListUsersUseCase, Depends(get_list_users_use_case)],
    page: Annotated[int, Query(gt=0)] = 1,
    limit: Annotated[int, Query(gt=-1, lt=101)] = 30,
    filter_by_name: str = '',
    sort_by: str = 'username',
    order_by: OrderByEnum = OrderByEnum.DESC,
):
    filters = {
        'page': page,
        'limit': limit,
        'filter_by_name': filter_by_name,
        'sort_by': sort_by,
        'order_by': order_by,
    }
    return await use_case(cur_user, filters)


@router.post('/me/upload_image', status_code=status.HTTP_200_OK, summary='Upload Image')
async def upload_avatar_image(
    cur_user: Annotated[User, Depends(get_current_user)],
    use_case: Annotated[UploadImageUseCase, Depends(get_upload_file_use_case)],
    file: UploadFile,
):
    file_bytes = await file.read()
    s3_filename = await use_case(cur_user, file_bytes)
    return {'image': s3_filename, 'status': 'uploaded'}


@router.delete('/{user_id}', status_code=status.HTTP_200_OK, summary='Delete User')
async def delete_user_as_admin(
    cur_user: Annotated[User, Depends(get_current_user)],
    user_id: str,
    use_case: Annotated[DeleteUserByIdUseCase, Depends(get_delete_by_id_use_case)],
):
    await use_case(cur_user, user_id)
    return {'message': f'user with id {user_id} deleted'}
