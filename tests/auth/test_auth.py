import pytest
from fastapi.testclient import TestClient

from src.config.settings import settings
from src.main import app
from tests.utils.fake_utils import generate_user
from tests.utils.database_setup import existed_user


client = TestClient(app)


def test_health_check():
    response = client.get('/health_check')
    assert response.status_code == 200
    assert response.json() == {'status': 'running'}


def test_root():
    response = client.get('/')
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_refresh_token(async_app_client):
    login_data = existed_user
    response = await async_app_client.post('auth/login', data=login_data)
    assert response.status_code == 200
    refresh_token = response.json().get('refresh_token')
    assert refresh_token
    headers = {'refresh-tkn': refresh_token}
    response = await async_app_client.post('auth/refresh-token', headers=headers)
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
    response = await async_app_client.post('/auth/signup', data=payload_with_pass)
    assert response.status_code == 201
    payload.update({'message': 'user created'})
    assert response.json() == payload


@pytest.mark.asyncio
async def test_create_with_invalid_password(async_app_client, create_fake_user):
    _, payload_with_pass = create_fake_user
    payload_with_pass['password'] = '<PASSWORD>'
    response = await async_app_client.post('/auth/signup', data=payload_with_pass)
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_create_5_users(async_app_client):
    for _ in range(5):
        user = generate_user()
        response = await async_app_client.post('/auth/signup', data=user[1])
        assert response.status_code == 201


@pytest.mark.asyncio
async def test_create_without_required_param(create_fake_user, async_app_client):
    payload, payload_with_pass = create_fake_user
    response = await async_app_client.post('/auth/signup', data=payload)
    assert response.status_code == 422
    del payload_with_pass['email']
    new_payload = payload_with_pass
    response = await async_app_client.post('/auth/signup', data=new_payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_with_invalid_params(create_fake_user, async_app_client):
    payload, payload_with_pass = create_fake_user
    payload_with_pass['email'] = 'not_an_email'
    response = await async_app_client.post('/auth/signup', data=payload_with_pass)
    assert response.status_code == 422
    payload, payload_with_pass = create_fake_user
    payload_with_pass['email'] = 'email@email.ru'
    payload_with_pass['phone'] = 'not_a_phone'
    new_payload = payload_with_pass
    response = await async_app_client.post('/auth/signup', data=new_payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_with_integration_error(create_fake_user, async_app_client):
    payload, payload_with_pass = create_fake_user
    response = await async_app_client.post('/auth/signup', data=payload_with_pass)
    assert response.status_code == 201
    payload.update({'message': 'user created'})
    assert response.json() == payload
    response = await async_app_client.post('/auth/signup', data=payload_with_pass)
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_create_with_image(create_fake_user, async_app_client, generate_jpg):
    _, payload_with_pass = create_fake_user
    image_path = generate_jpg
    with open(image_path, 'rb') as image:
        files = {'image': image}
        response = await async_app_client.post(
            '/auth/signup', data=payload_with_pass, files=files
        )
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_create_with_bad_passw(create_fake_user, async_app_client):
    _, payload_with_pass = create_fake_user
    payload_with_pass['password'] = '<PASSWORD>'
    response = await async_app_client.post('/auth/signup', data=payload_with_pass)
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_login(async_app_client):
    response = await async_app_client.post(
        '/auth/login', data={'username': settings.username, 'password': '12345678'}
    )
    assert response.status_code == 200
    assert response.json().get('type') == 'bearer'
    assert response.json().get('message') == 'Logged in successfully'


@pytest.mark.asyncio
async def test_login_blocked_user(async_app_client, create_blocked_user):
    login = create_blocked_user
    response = await async_app_client.post('/auth/login', data=login)
    assert response.status_code == 401
    assert response.json().get('detail') == 'User blocked'


@pytest.mark.asyncio
async def test_login_nonexistent_user(async_app_client):
    fake_login = {'username': 'non_exist', 'password': '<  blank  >'}
    response = await async_app_client.post('/auth/login', data=fake_login)
    assert response.status_code == 401
    assert response.json().get('detail') == 'User not found'


@pytest.mark.asyncio
async def test_login_with_incorrect_passw(async_app_client):
    login_data = existed_user.copy()
    login_data['password'] = 'fake_password'
    response = await async_app_client.post('/auth/login', data=login_data)
    assert response.status_code == 401
    assert response.json().get('detail') == "Password don't match"


@pytest.mark.asyncio
async def test_refresh_token_blacklisting(create_fake_user, async_app_client):
    login_data = existed_user.copy()
    response = await async_app_client.post('auth/login', data=login_data)
    assert response.status_code == 200
    refresh_token = response.json().get('refresh_token')
    assert refresh_token
    headers = {'refresh-tkn': refresh_token}
    response = await async_app_client.post('auth/refresh-token', headers=headers)
    assert response.status_code == 200
    response = await async_app_client.post('auth/refresh-token', headers=headers)
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_refresh_token_usability(async_app_client):
    login_data = existed_user.copy()
    response = await async_app_client.post('auth/login', data=login_data)
    assert response.status_code == 200
    refresh_token = response.json().get('refresh_token')
    headers = {'refresh-tkn': refresh_token}
    response = await async_app_client.post('auth/refresh-token', headers=headers)
    assert response.status_code == 200
    access_token = response.json().get('access_token')
    headers = {'Authorization': f'Bearer {access_token}'}
    response = await async_app_client.get('users/me', headers=headers)
    assert response.status_code == 200
    assert response.json().get('username') == existed_user['username']
