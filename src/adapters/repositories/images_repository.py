import io
import uuid
from io import BytesIO

import aioboto3
import magic
from botocore.exceptions import ClientError

from src.adapters.exceptions import (
    ImagesBucketError,
    NoFileContentError,
    FileSizeError,
    InvalidFileTypeError,
)
from src.adapters.config import logger
from src.config.settings import settings, MAX_FILE_SIZE, SUPPORTED_TYPES
from src.domain.entities.user import User
from src.ports.repositories.images_repository import ImagesRepository


class AWSS3ImagesRepository(ImagesRepository):
    async def _upload_image(
        self, content: BytesIO, filename: str, username: str
    ) -> str:
        session = aioboto3.Session()
        async with session.client(
            's3',
            endpoint_url=f'http://{settings.localstack_host}:4566',
            aws_access_key_id='test',
            aws_secret_access_key='test',
        ) as s3:
            await self._create_bucket_if_not_exists(s3)
            await self._delete_last_if_exceeds_5(s3, username)
            try:
                await s3.upload_fileobj(content, settings.bucket_name, filename)
            except Exception as e:
                logger.error(f'Error with trying to upload file: {e}')
                raise ImagesBucketError(e)
        return f's3://{settings.bucket_name}/{filename}'

    @staticmethod
    async def _create_bucket_if_not_exists(s3):
        try:
            await s3.head_bucket(Bucket=settings.bucket_name)
        except ClientError as e:
            logger.error(f'Error while trying to create bucket if not exist: {e}')
            await s3.create_bucket(Bucket=settings.bucket_name)
        except Exception as e:
            raise ImagesBucketError(e)

    @staticmethod
    async def _delete_last_if_exceeds_5(s3, email):
        objects = await s3.list_objects(Bucket=settings.bucket_name, Prefix=email)
        if (
            'Contents' in objects
            and objects.get('Contents')
            and len(objects.get('Contents')) > 4
        ):
            content = objects.get('Contents')
            to_delete = sorted(content, key=lambda x: x.get('LastModified'))[0]
            await s3.delete_object(Bucket=settings.bucket_name, Key=to_delete['Key'])

    async def upload_image(self, current_user: User, content: bytes | None) -> str:
        if not content:
            raise NoFileContentError('File not presented')

        file_size = len(content)
        if file_size < 1 or file_size > MAX_FILE_SIZE:
            raise FileSizeError('File size is too big or less than 1')

        file_type = magic.from_buffer(content, mime=True)
        if file_type not in SUPPORTED_TYPES:
            logger.error(f"Unsupported file type: {file_type}")
            raise InvalidFileTypeError(
                f'Unsupported file type {file_type}. Supported types: {SUPPORTED_TYPES}'
            )
        s3_filename = await self._upload_image(
            io.BytesIO(content),
            f'{current_user.username}/{uuid.uuid4()}.{SUPPORTED_TYPES[file_type]}',
            current_user.username,
        )
        return s3_filename
