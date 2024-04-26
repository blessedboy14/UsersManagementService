import datetime

from pydantic_settings import BaseSettings
import os
from dotenv import load_dotenv
import logging


load_dotenv()


class Settings(BaseSettings):
    passw: str = os.getenv('pass')
    username: str = os.getenv('name')
    postgres_host: str = os.getenv('POSTGRES_HOST')
    redis_host: str = os.getenv('REDIS_HOST')
    rabbit_host: str = os.getenv('RABBITMQ_HOST')
    bucket_name: str = os.getenv('BUCKET_NAME')
    localstack_host: str = os.getenv('LOCALSTACK_HOST')
    rabbit_queue: str = os.getenv('RABBITMQ_QUEUE')
    test_db: str = 'test_management_service'


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
handler = logging.FileHandler(f'logs/{datetime.datetime.today().date()}_log.log')
handler.setFormatter(formatter)

logger.addHandler(handler)

