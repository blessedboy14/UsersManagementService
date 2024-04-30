import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import insert

from src.database.models import UserDB, Group
from src.database.database import get_session, Base
from src.main import app
from tests.utils.database_setup import (
    get_test_session,
    base_user,
    test_session_maker,
    existed_user,
)
from tests.utils.fake_utils import generate_user

app.dependency_overrides[get_session] = get_test_session


@pytest_asyncio.fixture
async def async_app_client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url='https://localhost'
    ) as cli:
        yield cli


@pytest.fixture
def create_fake_user():
    return generate_user()


@pytest_asyncio.fixture(scope='session', autouse=True)
async def async_setup_and_tear_down(request):
    async with test_session_maker.get_engine().begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(
            insert(Group).values(
                {'name': 'testing', 'id': 'd9a83fd7-c45f-4c78-84eb-0922d6a5eec0'}
            )
        )
        await conn.execute(insert(UserDB).values(**base_user))
    yield

    async with test_session_maker.get_engine().begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_session_maker.close()


@pytest_asyncio.fixture
async def auth_main_user(async_app_client):
    response = await async_app_client.post('/auth/login', data=existed_user)
    assert response.status_code == 200
    access_token = response.json().get('access_token')
    return access_token


@pytest_asyncio.fixture
async def auth_fake_user(async_app_client, create_fake_user):
    payload, payload_with_pass = create_fake_user
    response = await async_app_client.post('/auth/signup', data=payload_with_pass)
    assert response.status_code == 201
    login_payload = {
        'username': payload['username'],
        'password': payload_with_pass['password'],
    }
    response = await async_app_client.post('/auth/login', data=login_payload)
    assert response.status_code == 200
    access_token = response.json().get('access_token')
    return access_token, login_payload


@pytest_asyncio.fixture
async def create_blocked_user(async_app_client, auth_fake_user, auth_main_user):
    access_token, login_payload = auth_fake_user
    headers = {'Authorization': f'Bearer {access_token}'}
    response = await async_app_client.get('/users/me', headers=headers)
    assert response.status_code == 200
    user_id = response.json().get('id')
    access_token = auth_main_user
    headers = {'Authorization': f'Bearer {access_token}'}
    to_update = {'is_blocked': 'true'}
    response = await async_app_client.patch(
        f'/users/{user_id}', headers=headers, json=to_update
    )
    assert response.status_code == 200
    return login_payload


@pytest_asyncio.fixture
async def create_moderator(async_app_client, auth_fake_user, auth_main_user):
    access_token, login_payload = auth_fake_user
    headers = {'Authorization': f'Bearer {access_token}'}
    response = await async_app_client.get('/users/me', headers=headers)
    assert response.status_code == 200
    user_id = response.json().get('id')
    access_token = auth_main_user
    headers = {'Authorization': f'Bearer {access_token}'}
    to_update = {'role': 'moderator'}
    response = await async_app_client.patch(
        f'/users/{user_id}', headers=headers, json=to_update
    )
    assert response.status_code == 200
    return access_token, login_payload
