import pytest
from fastapi.testclient import TestClient

from src.main import app
from tests.fixtures.auth_fixtures import generate_user, create_fake_user
from tests.fixtures.common_fixtures import async_app_client


client = TestClient(app)
existed_user = {'username': 'blessedboy', 'password': '12345678'}


def test_health_check():
    response = client.get('/health_check')
    assert response.status_code == 200
    assert response.json() == {'status': 'running'}


@pytest.mark.asyncio
async def test_refresh_token(async_app_client):
    login_data = existed_user
    async_client = async_app_client
    response = await async_client.post('auth/login', data=login_data)
    assert response.status_code == 200
    refresh_token = response.json().get('refresh_token')
    assert refresh_token
    headers = {'refresh-tkn': refresh_token}
    response = await async_client.post('auth/refresh-token', headers=headers)
    assert response.status_code == 200
    assert response.json().get('access_token')
    assert response.json().get('refresh_token')


@pytest.mark.asyncio
async def test_publishing_password_reset_message(async_app_client):
    to_reset_email = {'email': 'ewkere@email.com'}
    response = await async_app_client.post('auth/reset-password', json=to_reset_email)
    assert response.status_code == 200
    assert response.json().get('email') == to_reset_email.get('email')


@pytest.mark.asyncio
async def test_publish_reset_password_for_non_existing_user(async_app_client):
    to_reset_email = {'email': 'non@exist.com'}
    response = await async_app_client.post('auth/reset-password', json=to_reset_email)
    assert response.status_code == 404
    assert response.json().get('detail') == 'User not found'


@pytest.mark.asyncio
async def test_create_user(create_fake_user, async_app_client):
    payload, payload_with_pass = create_fake_user
    async_client = async_app_client
    response = await async_client.post('/auth/signup', data=payload_with_pass)
    assert response.status_code == 201
    assert response.json() == payload


@pytest.mark.asyncio
async def test_create_5_users(async_app_client):
    async_client = async_app_client
    for _ in range(5):
        user = generate_user()
        response = await async_client.post('/auth/signup', data=user[1])
        assert response.status_code == 201


@pytest.mark.asyncio
async def test_create_without_required_param(create_fake_user, async_app_client):
    payload, payload_with_pass = create_fake_user
    async_client = async_app_client
    response = await async_client.post('/auth/signup', data=payload)
    assert response.status_code == 422
    del payload_with_pass['email']
    new_payload = payload_with_pass
    response = await async_client.post('/auth/signup', data=new_payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_with_invalid_params(create_fake_user, async_app_client):
    payload, payload_with_pass = create_fake_user
    payload_with_pass['email'] = 'not_an_email'
    async_client = async_app_client
    response = await async_client.post('/auth/signup', data=payload_with_pass)
    assert response.status_code == 422
    payload, payload_with_pass = create_fake_user
    payload_with_pass['email'] = 'email@email.ru'
    payload_with_pass['phone'] = 'not_a_phone'
    new_payload = payload_with_pass
    response = await async_client.post('/auth/signup', data=new_payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_integration_error(create_fake_user, async_app_client):
    payload, payload_with_pass = create_fake_user
    async_client = async_app_client
    response = await async_client.post('/auth/signup', data=payload_with_pass)
    assert response.status_code == 201
    assert response.json() == payload
    response = await async_client.post('/auth/signup', data=payload_with_pass)
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_create_then_login_then_delete(create_fake_user, async_app_client):
    payload, payload_with_pass = create_fake_user
    async_client = async_app_client
    response = await async_client.post('/auth/signup', data=payload_with_pass)
    assert response.status_code == 201
    assert response.json() == payload
    login_data = {
        'username': payload['username'],
        'password': payload_with_pass['password'],
    }
    response = await async_client.post('/auth/login', data=login_data)
    assert response.status_code == 200
    access_token = response.json()['access_token']
    assert access_token
    headers = {'Authorization': f'Bearer {access_token}'}
    response = await async_client.delete('/users/me', headers=headers)
    assert response.status_code == 200
    assert response.json() == {'message': 'User deleted', 'data': None}


@pytest.mark.asyncio
async def test_login(async_app_client):
    async_client = async_app_client
    response = await async_client.post(
        '/auth/login', data={'username': 'blessedboy', 'password': '12345678'}
    )
    assert response.status_code == 200
    assert response.json().get('type') == 'bearer'


@pytest.mark.asyncio
async def test_login_nonexistent_user(async_app_client):
    fake_login = {'username': 'non_exist', 'password': '<  blank  >'}
    async_client = async_app_client
    response = await async_client.post('/auth/login', data=fake_login)
    assert response.status_code == 401
    assert response.json().get('detail') == 'User not found'


@pytest.mark.asyncio
async def test_login_with_incorrect_passw(async_app_client):
    login_data = existed_user.copy()
    login_data['password'] = 'fake_password'
    async_client = async_app_client
    response = await async_client.post('/auth/login', data=login_data)
    assert response.status_code == 401
    assert response.json().get('detail') == "Password don't match"


@pytest.mark.asyncio
async def test_refresh_token_blacklisting(create_fake_user, async_app_client):
    login_data = existed_user.copy()
    async_client = async_app_client
    response = await async_client.post('auth/login', data=login_data)
    assert response.status_code == 200
    refresh_token = response.json().get('refresh_token')
    assert refresh_token
    headers = {'refresh-tkn': refresh_token}
    response = await async_client.post('auth/refresh-token', headers=headers)
    assert response.status_code == 200
    response = await async_client.post('auth/refresh-token', headers=headers)
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_refresh_token_usability(async_app_client):
    login_data = existed_user.copy()
    async_client = async_app_client
    response = await async_client.post('auth/login', data=login_data)
    assert response.status_code == 200
    refresh_token = response.json().get('refresh_token')
    headers = {'refresh-tkn': refresh_token}
    response = await async_client.post('auth/refresh-token', headers=headers)
    assert response.status_code == 200
    access_token = response.json().get('access_token')
    headers = {'Authorization': f'Bearer {access_token}'}
    response = await async_client.get('users/me', headers=headers)
    print(response.json())
    assert response.status_code == 200
    assert response.json().get('username') == existed_user['username']
