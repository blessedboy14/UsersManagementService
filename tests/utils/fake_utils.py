import random
import string

from faker import Faker


fake = Faker('ru_RU')


def fake_phone():
    setup = '+37529'
    for _ in range(7):
        setup += str(random.randint(1, 9))
    return setup


def fake_password():
    min, max = 8, 20
    chars = string.ascii_lowercase + string.digits + string.punctuation
    pasw = ''
    pasw += (
        random.choice(string.ascii_lowercase)
        + random.choice(string.digits)
        + random.choice(string.punctuation)
    )
    for _ in range(random.randint(min, max) - 3):
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
