import uuid
from fastapi import UploadFile
from fastapi.exceptions import HTTPException
import os
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth import service
from src.auth.service import login_user, get_user, send_reset_password_message
from src.auth.models import TokenSchema, LoginUser, ResetPasswordRequest
from src.database.database import get_session
from src.database.models import UserDB
from src.auth.security import get_password_hash, create_access_jwt
from src.rabbitmq.publisher import publisher
from src.users import users
from src.users.service import _create_bucket_if_not_exists, upload_image
from src.users.users import get_current_user
from tests.utils.database_setup import existed_user, test_session_maker


@pytest.mark.asyncio
async def test_get_session():
    actual = await anext(get_session())
    assert isinstance(actual, AsyncSession)


@pytest.mark.asyncio
async def test_login_service(monkeypatch):
    mock_user = LoginUser(login='mock@email.com', password='_s1dsadxccc')
    mocked_db_user = UserDB(
        email=mock_user.login,
        username='mocked_usr',
        is_blocked=False,
        phone='+375291234567',
        hashed_password=get_password_hash('_s1dsadxccc'),
        id=uuid.uuid4(),
    )

    async def mock_login(*args, **kwargs):
        return TokenSchema(
            message='empty',
            access_token='<PASSWORD>',
            refresh_token='<PASSWORD>',
            type='bearer',
        )

    async def mock_get_user(*args, **kwargs):
        return mocked_db_user

    monkeypatch.setattr(service, 'login_user', mock_login)
    monkeypatch.setattr(service, 'get_user', mock_get_user)

    result = await login_user(mock_user, AsyncSession())
    assert result.message == 'Logged in successfully'

    mocked_db_user.hashed_password = get_password_hash('<PASSWORD>')

    async def mock_get_user_bad_passw(*args, **kwargs):
        return mocked_db_user

    monkeypatch.setattr(service, 'get_user', mock_get_user_bad_passw)
    try:
        _ = await login_user(mock_user, AsyncSession())
    except Exception as exc:
        assert isinstance(exc, HTTPException)


@pytest.mark.asyncio
async def test_get_user():
    usr = LoginUser(login=existed_user['username'], password=existed_user['password'])
    session = await anext(test_session_maker.create_session().gen)
    result = await get_user(usr, session)
    assert result.username == existed_user['username']
    await session.close()


@pytest.mark.asyncio
async def test_send_reset_message(monkeypatch):
    mocked_db_user = UserDB(
        email='test@mail.ru',
        username='mocked_usr',
        is_blocked=False,
        phone='+375291234567',
        hashed_password=get_password_hash('_s1dsadxccc'),
        id=uuid.uuid4(),
    )

    async def mock_get_by_email(*args, **kwargs):
        return mocked_db_user

    def mock_publish_message(*args, **kwargs):
        return

    monkeypatch.setattr(publisher, 'publish_message', mock_publish_message)
    monkeypatch.setattr(service, 'get_by_email', mock_get_by_email)

    result = await send_reset_password_message(
        ResetPasswordRequest(email='test@mail.ru'), AsyncSession()
    )

    assert result.message == 'message for resetting sent to rabbitmq'


@pytest.mark.asyncio
async def test_fetch_user_from_token_without_id():
    fake_token = create_access_jwt({})
    try:
        _ = await get_current_user(fake_token, AsyncSession())
    except Exception as exc:
        assert isinstance(exc, HTTPException)


@pytest.mark.asyncio
async def test_fetch_non_exist_id_from_token():
    session = await anext(test_session_maker.create_session().gen)
    fake_id = str(uuid.uuid4())
    fake_token = create_access_jwt({'user_id': fake_id})
    try:
        _ = await get_current_user(fake_token, session)
    except Exception as exc:
        assert isinstance(exc, HTTPException)
    finally:
        await session.close()


@pytest.mark.asyncio
async def test_create_bucket_error():
    try:
        _ = await _create_bucket_if_not_exists(None)
    except Exception as e:
        assert isinstance(e, HTTPException)


@pytest.mark.asyncio
async def test_file_uploading_errors(monkeypatch):
    async def mock_upload_file(*args, **kwargs):
        return

    monkeypatch.setattr(users.service, 'upload_to_s3_bucket', mock_upload_file)

    try:
        _ = await upload_image(None, 'blank')
    except Exception as e:
        assert isinstance(e, HTTPException)

    open('empty.txt', 'wb').close()
    with open('empty.txt', 'rb') as f:
        try:
            _ = await upload_image(UploadFile(f), 'blank')
        except Exception as e:
            assert isinstance(e, HTTPException)

    with open('empty.txt', 'w') as f:
        f.write('hello')

    with open('empty.txt', 'rb') as f:
        try:
            _ = await upload_image(UploadFile(f), 'blank')
        except Exception as e:
            assert isinstance(e, HTTPException)

    os.remove('empty.txt')
