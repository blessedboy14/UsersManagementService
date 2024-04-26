from fastapi import HTTPException
from starlette import status

from src.config.settings import logger


def raise_credential_exception(message: str):
    logger.error(f'Credential exception with tokens: {message}')
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=message,
        headers={'WWW-Authenticate': 'Bearer'},
    )


def raise_upload_exception(msg: str):
    logger.error(f'Upload image exception with message: {msg}')
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)
