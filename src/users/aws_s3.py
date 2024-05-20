from io import BytesIO

import aioboto3
from botocore.exceptions import ClientError
from fastapi import HTTPException
from starlette import status

from src.config.settings import settings, logger


async def _create_bucket_if_not_exists(s3):
    try:
        await s3.head_bucket(Bucket=settings.bucket_name)
    except ClientError as e:
        logger.error(f'error while trying to create bucket if not exist: {e}')
        await s3.create_bucket(Bucket=settings.bucket_name)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


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


async def upload_to_s3_bucket(content: BytesIO, filename: str, username: str) -> str:
    session = aioboto3.Session()
    logger.debug('uploading file to bucket')
    async with session.client(
        's3',
        endpoint_url=f'http://{settings.localstack_host}:4566',
        aws_access_key_id='test',
        aws_secret_access_key='test',
    ) as s3:
        await _create_bucket_if_not_exists(s3)
        await _delete_last_if_exceeds_5(s3, username)
        try:
            await s3.upload_fileobj(content, settings.bucket_name, filename)
        except Exception as e:
            logger.error(f'error while trying to upload file: {e}')
            raise e
    return f's3://{settings.bucket_name}/{filename}'
