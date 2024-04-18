import random
import pytest
import string

import pytest_asyncio
from fastapi.testclient import TestClient
from fastapi.security import OAuth2PasswordRequestForm
from httpx import AsyncClient
from src.main import app
from faker import Faker


client = TestClient(app)

fake = Faker("ru_RU")


@pytest_asyncio.fixture
async def async_app_client():
    async with AsyncClient(app=app, base_url="https://localhost") as cli:
        yield cli


def test_health_check():
    response = client.get("/health_check")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def fake_phone():
    setup = "+37529"
    for _ in range(7):
        setup += str(random.randint(1, 9))
    return setup


def fake_password():
    min, max = 8, 20
    chars = string.ascii_letters + string.digits
    pasw = ""
    for _ in range(random.randint(min, max)):
        pasw += chars[random.randint(0, len(chars) - 1)]
    return pasw


def test_create_user(create_fake_user):
    payload, payload_with_pass = create_fake_user
    response = client.post("/auth/signup", json=payload_with_pass)
    assert response.status_code == 201
    assert response.json() == payload


@pytest.fixture()
def create_fake_user():
    payload = {
        "email": fake.email(),
        "phone": fake_phone(),
        "username": fake.user_name(),
    }
    payload_with_pass = {
        **payload,
        "password": fake_password()
    }
    return payload, payload_with_pass
