from sqlalchemy import URL
from pydantic_settings import BaseSettings
import os
from dotenv import load_dotenv


load_dotenv()


class Settings(BaseSettings):
    passw: str = "ewkere123"
    username: str = "blessedboy"
    postgres_host: str = os.getenv("POSTGRES_HOST")
    redis_host: str = os.getenv("REDIS_HOST")
    rabbit_host: str = os.getenv("RABBITMQ_HOST")
    bucket_name: str = "images-storage"
    localstack_host: str = os.getenv("LOCALSTACK_HOST")


settings = Settings()

db_username = settings.username
db_password = settings.passw
db_url = f"{settings.postgres_host}:5432"
db_schema = "management_service"

url = URL.create(
    drivername="postgresql+asyncpg",
    username=db_username,
    password=db_password,
    host=db_url,
    database=db_schema,
)

string_url = f"postgresql+asyncpg://{db_username}:{db_password}@{db_url}/{db_schema}"

MAX_FILE_SIZE = 1024 * 1024 * 20

SUPPORTED_TYPES = {
    'image/png': 'png',
    'image/jpeg': 'jpg'
}
