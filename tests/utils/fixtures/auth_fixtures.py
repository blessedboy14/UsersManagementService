import random
import string

import pytest
from faker import Faker


fake = Faker('ru_RU')


@pytest.fixture
def create_fake_user():
    return generate_user()


def fake_phone():
    setup = '+37529'
    for _ in range(7):
        setup += str(random.randint(1, 9))
    return setup


def fake_password():
    min, max = 8, 20
    chars = string.ascii_letters + string.digits
    pasw = ''
    for _ in range(random.randint(min, max)):
        pasw += chars[random.randint(0, len(chars) - 1)]
    return pasw


def generate_user():
    payload = {
        'email': fake.email(),
        'phone': fake_phone(),
        'username': fake.user_name(),
    }
    payload_with_pass = {**payload, 'password': fake_password()}
    return payload, payload_with_pass


@pytest.fixture(scope='session', autouse=True)
async def create_start_user(async_app_client):
    client = async_app_client
    data = {
        'email': 'ewkere@email.com',
        'phone': '+375298057993',
        'username': 'blessedboy',
        'password': '12345678',
    }
    response = await client.post('/auth/signup', data=data)
    assert response.status_code == 200
