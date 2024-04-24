import faker
import pytest
from httpx import AsyncClient

from tests.utils.database.setup import existed_user
from tests.utils.fixtures.common_fixtures import async_app_client
from tests.utils.fixtures.auth_fixtures import create_fake_user


async def _auth(client: AsyncClient):
    response = await client.post('/auth/login', data=existed_user)
    assert response.status_code == 200
    access_token = response.json().get('access_token')
    return access_token


async def _auth_fake_user(client: AsyncClient, create_fake_user):
    payload, payload_with_pass = create_fake_user
    response = await client.post('/auth/signup', data=payload_with_pass)
    assert response.status_code == 201
    login_payload = {
        'username': payload['username'],
        'password': payload_with_pass['password'],
    }
    response = await client.post('/auth/login', data=login_payload)
    assert response.status_code == 200
    access_token = response.json().get('access_token')
    return access_token, login_payload


@pytest.mark.asyncio
async def test_read_existed_user(async_app_client):
    client = async_app_client
    access_token = await _auth(client)
    headers = {'Authorization': f'Bearer {access_token}'}
    response = await client.get('users/me', headers=headers)
    assert response.status_code == 200
    assert response.json().get('username') == existed_user.get('username')


@pytest.mark.asyncio
async def test_read_with_invalid_token(async_app_client):
    client = async_app_client
    _ = await _auth(client)
    headers = {'Authorization': 'Bearer not_valid_token'}
    response = await client.get('users/me', headers=headers)
    assert response.status_code == 401
    assert response.json().get('detail') == 'Token invalid'


@pytest.mark.asyncio
async def test_read_without_token(async_app_client):
    client = async_app_client
    _ = await _auth(client)
    response = await client.get('users/me')
    assert response.status_code == 401
    assert response.json().get('detail') == 'Not authenticated'


@pytest.mark.asyncio
async def test_create_then_login_then_delete(create_fake_user, async_app_client):
    async_client = async_app_client
    access_token, _ = await _auth_fake_user(async_client, create_fake_user)
    assert access_token
    headers = {'Authorization': f'Bearer {access_token}'}
    response = await async_client.delete('/users/me', headers=headers)
    assert response.status_code == 200
    assert response.json() == {'message': 'User deleted', 'data': None}


@pytest.mark.asyncio
async def test_create_then_login_then_delete_then_login(
    create_fake_user, async_app_client
):
    async_client = async_app_client
    access_token, login_data = await _auth_fake_user(async_client, create_fake_user)
    assert access_token
    headers = {'Authorization': f'Bearer {access_token}'}
    response = await async_client.delete('/users/me', headers=headers)
    assert response.status_code == 200
    assert response.json() == {'message': 'User deleted', 'data': None}
    response = await async_client.post('/auth/login', data=login_data)
    assert response.status_code == 401
    assert response.json().get('detail') == 'User not found'


@pytest.mark.asyncio
async def test_patch_existed_user_email_and_then_login(
    create_fake_user, async_app_client
):
    client = async_app_client
    access_token, login = await _auth_fake_user(client, create_fake_user)
    to_patch = {
        'email': faker.Faker().email(),
    }
    headers = {'Authorization': f'Bearer {access_token}'}
    response = await client.patch('/users/me', json=to_patch, headers=headers)
    assert response.status_code == 200
    assert response.json().get('email') == to_patch.get('email')
    login['email'] = to_patch.get('email')
    response = await client.post('/auth/login', data=login)
    assert response.status_code == 200
    access_token = response.json().get('access_token')
    headers = {'Authorization': f'Bearer {access_token}'}
    response = await client.get('/users/me', headers=headers)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_patch_non_existing_property(create_fake_user, async_app_client):
    client = async_app_client
    access_token, login = await _auth_fake_user(client, create_fake_user)
    to_patch = {'fake_prop': 'fake_info'}
    headers = {'Authorization': f'Bearer {access_token}'}
    response = await client.patch('/users/me', json=to_patch, headers=headers)
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_read_all_users_by_id(async_app_client):
    client = async_app_client
    access_token = await _auth(client)
    headers = {'Authorization': f'Bearer {access_token}'}
    response = await client.get('/users', headers=headers)
    assert response.status_code == 200
    assert len(response.json()) > 0
    users = response.json()
    for user in users:
        user_id = user.get('id')
        response = await client.get(f'/users/{user_id}', headers=headers)
        assert response.status_code == 200
        assert response.json().get('id') == user_id


@pytest.mark.asyncio
async def test_read_user_with_invalid_id(async_app_client):
    client = async_app_client
    access_token = await _auth(client)
    headers = {'Authorization': f'Bearer {access_token}'}
    response = await client.get('/users/fake_id123', headers=headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_user_listing_without_filtering(async_app_client):
    client = async_app_client
    access_token = await _auth(client)
    headers = {'Authorization': f'Bearer {access_token}'}
    response = await client.get('/users', headers=headers)
    assert response.status_code == 200
    assert len(response.json()) > 0


@pytest.mark.asyncio
async def test_list_users_with_filter_by_role(async_app_client):
    client = async_app_client
    access_token = await _auth(client)
    headers = {'Authorization': f'Bearer {access_token}'}
    response = await client.get(
        '/users',
        headers=headers,
        params={'page': '1', 'limit': '11', 'sort_by': 'role', 'order_by': 'desc'},
    )
    assert response.status_code == 200
    assert len(response.json()) > 0
    users = response.json()
    assert users[0].get('role') == 'user'


@pytest.mark.asyncio
async def test_list_users_with_non_existed_page(async_app_client):
    client = async_app_client
    access_token = await _auth(client)
    headers = {'Authorization': f'Bearer {access_token}'}
    response = await client.get(
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
async def test_list_users_with_zero_limit(async_app_client):
    client = async_app_client
    access_token = await _auth(client)
    headers = {'Authorization': f'Bearer {access_token}'}
    response = await client.get(
        '/users',
        headers=headers,
        params={
            'limit': '0',
        },
    )
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_list_users_with_non_existed_sort_by(async_app_client):
    client = async_app_client
    access_token = await _auth(client)
    headers = {'Authorization': f'Bearer {access_token}'}
    response = await client.get(
        '/users', headers=headers, params={'sort_by': 'fake_field'}
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_patch_random_user_as_admin(async_app_client):
    client = async_app_client
    access_token = await _auth(client)
    headers = {'Authorization': f'Bearer {access_token}'}
    response = await client.get('/users', headers=headers)
    assert response.status_code == 200
    user = response.json()[0]
    user_id = user.get('id')
    to_patch = {'name': 'patchedName'}
    response = await client.patch(f'/users/{user_id}', headers=headers, json=to_patch)
    assert response.status_code == 200
    assert response.json().get('name') == to_patch['name']
    response = await client.get(f'users/{user_id}', headers=headers)
    assert response.status_code == 200
    assert response.json().get('name') == to_patch['name']


@pytest.mark.asyncio
async def test_patch_random_user_to_admin(async_app_client):
    client = async_app_client
    access_token = await _auth(client)
    headers = {'Authorization': f'Bearer {access_token}'}
    response = await client.get('/users', headers=headers)
    assert response.status_code == 200
    user = response.json()[0]
    user_id = user.get('id')
    to_patch = {'role': 'admin'}
    response = await client.patch(f'/users/{user_id}', headers=headers, json=to_patch)
    assert response.status_code == 200
    assert response.json().get('role') == to_patch['role']
    response = await client.get(
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
async def test_file_uploading(async_app_client):
    client = async_app_client
    access_token = await _auth(client)
    headers = {'Authorization': f'Bearer {access_token}'}
    path_to_file = '/home/blessedboy/Downloads/phon.jpg'
    with open(path_to_file, 'rb') as f:
        response = await client.post(
            '/users/me/upload_image',
            files={'file': ('filename', f, 'image/jpeg')},
            headers=headers,
        )
    assert response.status_code == 200
