import uuid

import faker
import pytest

from tests.utils.database_setup import existed_user


@pytest.mark.asyncio
async def test_read_existed_user(async_app_client, auth_main_user):
    access_token = auth_main_user
    headers = {'Authorization': f'Bearer {access_token}'}
    response = await async_app_client.get('users/me', headers=headers)
    assert response.status_code == 200
    assert response.json().get('username') == existed_user.get('username')


@pytest.mark.asyncio
async def test_read_with_invalid_token(async_app_client, auth_main_user):
    _ = auth_main_user
    headers = {'Authorization': 'Bearer not_valid_token'}
    response = await async_app_client.get('users/me', headers=headers)
    assert response.status_code == 401
    assert response.json().get('detail') == 'Token invalid'


@pytest.mark.asyncio
async def test_read_without_token(async_app_client, auth_main_user):
    _ = auth_main_user
    response = await async_app_client.get('users/me')
    assert response.status_code == 401
    assert response.json().get('detail') == 'Not authenticated'


@pytest.mark.asyncio
async def test_create_then_login_then_delete(
    create_fake_user, async_app_client, auth_fake_user
):
    access_token, _ = auth_fake_user
    assert access_token
    headers = {'Authorization': f'Bearer {access_token}'}
    response = await async_app_client.delete('/users/me', headers=headers)
    assert response.status_code == 200
    assert response.json() == {'message': 'User deleted', 'data': None}


@pytest.mark.asyncio
async def test_create_then_login_then_delete_then_login(
    create_fake_user, async_app_client, auth_fake_user
):
    access_token, login_data = auth_fake_user
    assert access_token
    headers = {'Authorization': f'Bearer {access_token}'}
    response = await async_app_client.delete('/users/me', headers=headers)
    assert response.status_code == 200
    assert response.json() == {'message': 'User deleted', 'data': None}
    response = await async_app_client.post('/auth/login', data=login_data)
    assert response.status_code == 401
    assert response.json().get('detail') == 'User not found'


@pytest.mark.asyncio
async def test_patch_existed_user_email_and_then_login(
    create_fake_user, async_app_client, auth_fake_user
):
    access_token, login = auth_fake_user
    to_patch = {
        'email': faker.Faker().email(),
    }
    headers = {'Authorization': f'Bearer {access_token}'}
    response = await async_app_client.patch('/users/me', json=to_patch, headers=headers)
    assert response.status_code == 200
    assert response.json().get('email') == to_patch.get('email')
    login['email'] = to_patch.get('email')
    response = await async_app_client.post('/auth/login', data=login)
    assert response.status_code == 200
    access_token = response.json().get('access_token')
    headers = {'Authorization': f'Bearer {access_token}'}
    response = await async_app_client.get('/users/me', headers=headers)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_patch_non_existing_property(
    create_fake_user, async_app_client, auth_fake_user
):
    access_token, login = auth_fake_user
    to_patch = {'fake_prop': 'fake_info'}
    headers = {'Authorization': f'Bearer {access_token}'}
    response = await async_app_client.patch('/users/me', json=to_patch, headers=headers)
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_read_all_users_by_id(async_app_client, auth_main_user):
    access_token = auth_main_user
    headers = {'Authorization': f'Bearer {access_token}'}
    response = await async_app_client.get('/users', headers=headers)
    assert response.status_code == 200
    assert len(response.json()) > 0
    users = response.json()
    for user in users:
        user_id = user.get('id')
        response = await async_app_client.get(f'/users/{user_id}', headers=headers)
        assert response.status_code == 200
        assert response.json().get('id') == user_id


@pytest.mark.asyncio
async def test_read_user_with_invalid_id(async_app_client, auth_main_user):
    client = async_app_client
    access_token = auth_main_user
    headers = {'Authorization': f'Bearer {access_token}'}
    response = await client.get('/users/fake_id123', headers=headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_user_listing_without_filtering(async_app_client, auth_main_user):
    access_token = auth_main_user
    headers = {'Authorization': f'Bearer {access_token}'}
    response = await async_app_client.get('/users', headers=headers)
    assert response.status_code == 200
    assert len(response.json()) > 0


@pytest.mark.asyncio
async def test_list_users_with_filter_by_role(async_app_client, auth_main_user):
    access_token = auth_main_user
    headers = {'Authorization': f'Bearer {access_token}'}
    response = await async_app_client.get(
        '/users',
        headers=headers,
        params={'page': '1', 'limit': '11', 'sort_by': 'role', 'order_by': 'desc'},
    )
    assert response.status_code == 200
    assert len(response.json()) > 0
    users = response.json()
    assert users[0].get('role') == 'user'


@pytest.mark.asyncio
async def test_list_users_with_non_existed_page(async_app_client, auth_main_user):
    access_token = auth_main_user
    headers = {'Authorization': f'Bearer {access_token}'}
    response = await async_app_client.get(
        '/users',
        headers=headers,
        params={
            'page': '1000000',
            'limit': '11',
            'sort_by': 'role',
            'order_by': 'desc',
        },
    )
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_list_users_with_zero_limit(async_app_client, auth_main_user):
    access_token = auth_main_user
    headers = {'Authorization': f'Bearer {access_token}'}
    response = await async_app_client.get(
        '/users',
        headers=headers,
        params={
            'limit': '0',
        },
    )
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_list_users_with_non_existed_sort_by(async_app_client, auth_main_user):
    access_token = auth_main_user
    headers = {'Authorization': f'Bearer {access_token}'}
    response = await async_app_client.get(
        '/users', headers=headers, params={'sort_by': 'fake_field'}
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_patch_random_user_as_admin(async_app_client, auth_main_user):
    access_token = auth_main_user
    headers = {'Authorization': f'Bearer {access_token}'}
    response = await async_app_client.get('/users', headers=headers)
    assert response.status_code == 200
    user = response.json()[0]
    user_id = user.get('id')
    to_patch = {'name': 'patchedName'}
    response = await async_app_client.patch(
        f'/users/{user_id}', headers=headers, json=to_patch
    )
    assert response.status_code == 200
    assert response.json().get('name') == to_patch['name']
    response = await async_app_client.get(f'users/{user_id}', headers=headers)
    assert response.status_code == 200
    assert response.json().get('name') == to_patch['name']


@pytest.mark.asyncio
async def test_patch_random_user_to_admin(async_app_client, auth_main_user):
    access_token = auth_main_user
    headers = {'Authorization': f'Bearer {access_token}'}
    response = await async_app_client.get('/users', headers=headers)
    assert response.status_code == 200
    user = response.json()[0]
    user_id = user.get('id')
    to_patch = {'role': 'admin'}
    response = await async_app_client.patch(
        f'/users/{user_id}', headers=headers, json=to_patch
    )
    assert response.status_code == 200
    assert response.json().get('role') == to_patch['role']
    response = await async_app_client.get(
        'users',
        headers=headers,
        params={
            'filter_by_name': user.get('name'),
            'sort_by': 'role',
            'order_by': 'asc',
        },
    )
    assert response.status_code == 200
    usr = [usr for usr in response.json() if usr.get('name') == user.get('name')][0]
    assert usr
    assert usr.get('role') == 'admin'


@pytest.mark.asyncio
async def test_patch_with_integrity_error(
    async_app_client, auth_main_user, auth_fake_user
):
    access_token, payload = auth_fake_user
    headers = {'Authorization': f'Bearer {access_token}'}
    user_id = (
        (await async_app_client.get('/users/me', headers=headers)).json().get('id')
    )
    access_token = auth_main_user
    headers = {'Authorization': f'Bearer {access_token}'}
    to_patch = {'email': 'ewkere@email.com'}
    response = await async_app_client.patch(
        f'/users/{user_id}', headers=headers, json=to_patch
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_request_filter_as_user(async_app_client, auth_fake_user):
    access_token, _ = auth_fake_user
    headers = {'Authorization': f'Bearer {access_token}'}
    response = await async_app_client.get('/users', headers=headers)
    assert response.status_code == 405
    assert response.json().get('detail') == 'Not allowed'


@pytest.mark.asyncio
async def test_list_users_as_moder(async_app_client, create_moderator):
    access_token, _ = create_moderator
    headers = {'Authorization': f'Bearer {access_token}'}
    response = await async_app_client.get('/users', headers=headers)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_by_id_as_user(async_app_client, auth_fake_user):
    access_token, _ = auth_fake_user
    headers = {'Authorization': f'Bearer {access_token}'}
    response = await async_app_client.get(
        f'/users/{str(uuid.uuid4())}', headers=headers
    )
    assert response.status_code == 405


@pytest.mark.asyncio
async def test_get_by_id_as_moder(async_app_client, create_moderator):
    access_token, _ = create_moderator
    headers = {'Authorization': f'Bearer {access_token}'}
    response = await async_app_client.get('/users', headers=headers)
    assert response.status_code == 200
    user_id = response.json()[0].get('id')
    response = await async_app_client.get(f'/users/{user_id}', headers=headers)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_by_id_non_exist_id(
    async_app_client, auth_main_user, create_moderator
):
    user_id = str(uuid.uuid4())
    access_token, _ = create_moderator
    headers = {'Authorization': f'Bearer {access_token}'}
    response = await async_app_client.get(f'/users/{user_id}', headers=headers)
    assert response.status_code == 404
    access_token = auth_main_user
    headers = {'Authorization': f'Bearer {access_token}'}
    response = await async_app_client.get(f'/users/{user_id}', headers=headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_file_uploading(async_app_client, auth_main_user):
    access_token = auth_main_user
    headers = {'Authorization': f'Bearer {access_token}'}
    path_to_file = 'tests/auth/test.jpg'
    with open(path_to_file, 'rb') as f:
        response = await async_app_client.post(
            '/users/me/upload_image',
            files={'file': ('filename', f, 'image/jpeg')},
            headers=headers,
        )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_delete_user_as_admin(async_app_client, auth_main_user, auth_fake_user):
    access_token, _ = auth_fake_user
    headers = {'Authorization': f'Bearer {access_token}'}
    response = await async_app_client.get('/users/me', headers=headers)
    user_id = response.json().get('id')
    access_token = auth_main_user
    headers = {'Authorization': f'Bearer {access_token}'}
    response = await async_app_client.delete(f'/users/{user_id}', headers=headers)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_delete_as_non_admin(async_app_client, auth_fake_user):
    access_token, _ = auth_fake_user
    headers = {'Authorization': f'Bearer {access_token}'}
    response = await async_app_client.delete(
        f'/users/{str(uuid.uuid4())}', headers=headers
    )
    assert response.status_code == 405


@pytest.mark.asyncio
async def test_patch_non_exist_user(async_app_client, auth_main_user):
    access_token = auth_main_user
    headers = {'Authorization': f'Bearer {access_token}'}
    to_patch = {}
    response = await async_app_client.patch(
        f'/users/{str(uuid.uuid4())}', headers=headers, json=to_patch
    )
    assert response.status_code == 400
    assert response.json().get('detail') == 'User not found'


@pytest.mark.asyncio
async def test_patch_with_no_info(async_app_client, auth_main_user):
    access_token = auth_main_user
    headers = {'Authorization': f'Bearer {access_token}'}
    to_patch = {}
    user_id = (
        (await async_app_client.get('/users/me', headers=headers)).json().get('id')
    )
    response = await async_app_client.patch(
        f'/users/{user_id}', headers=headers, json=to_patch
    )
    assert response.status_code == 400
    assert response.json().get('detail') == 'No info provided or non-existing fields'
