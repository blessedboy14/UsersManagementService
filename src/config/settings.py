import datetime

from pydantic_settings import BaseSettings
import os
from dotenv import load_dotenv
import logging


load_dotenv()


class Settings(BaseSettings):
    passw: str = os.getenv('PASS') if os.getenv('PASS') else 'error'
    username: str = os.getenv('NAME') if os.getenv('NAME') else 'admin'
    postgres_host: str = (
        os.getenv('POSTGRES_HOST') if os.getenv('POSTGRES_HOST') else 'localhost'
    )
    test_postgres_host: str = (
        os.getenv('TEST_POSTGRES_HOST')
        if os.getenv('TEST_POSTGRES_HOST')
        else 'localhost'
    )
    test_db_port: str = (
        os.getenv('TEST_DB_PORT') if os.getenv('TEST_DB_PORT') else '5433'
    )
    redis_host: str = (
        os.getenv('REDIS_HOST') if os.getenv('REDIS_HOST') else 'localhost'
    )
    rabbit_host: str = (
        os.getenv('RABBITMQ_HOST') if os.getenv('RABBITMQ_HOST') else 'localhost'
    )
    bucket_name: str = (
        os.getenv('BUCKET_NAME') if os.getenv('BUCKET_NAME') else 'images-storage'
    )
    localstack_host: str = (
        os.getenv('LOCALSTACK_HOST') if os.getenv('LOCALSTACK_HOST') else 'localhost'
    )
    rabbit_queue: str = (
        os.getenv('RABBITMQ_QUEUE')
        if os.getenv('RABBITMQ_QUEUE')
        else 'reset-password-stream'
    )
    test_db: str = 'test_management_service'
    secret_key: str = os.getenv('SECRET_KEY') if os.getenv('SECRET_KEY') else '<KEY>'
    algorithm: str = os.getenv('ALGORITHM') if os.getenv('ALGORITHM') else 'HS256'
    access_exp: int = os.getenv('ACCESS_EXP') if os.getenv('ACCESS_EXP') else 60
    refresh_exp: int = os.getenv('REFRESH_EXP') if os.getenv('REFRESH_EXP') else 31


settings = Settings()

db_username = settings.username
db_password = settings.passw
db_url = f'{settings.postgres_host}:5432'
db_schema = 'management_service'
db_driver = 'postgresql+asyncpg'


string_url = f'{db_driver}://{db_username}:{db_password}@{db_url}/{db_schema}'

# uploading files settings
MAX_FILE_SIZE = 1024 * 1024 * 20
SUPPORTED_TYPES = {'image/png': 'png', 'image/jpeg': 'jpg'}


# logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
try:
    handler = logging.FileHandler(f'logs/{datetime.datetime.today().date()}_log.log')
except FileNotFoundError:
    handler = logging.StreamHandler()
handler.setFormatter(formatter)

logger.addHandler(handler)
