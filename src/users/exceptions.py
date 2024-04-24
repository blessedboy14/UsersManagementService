from fastapi import HTTPException
from starlette import status


def raise_credential_exception(message: str):
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=message,
        headers={'WWW-Authenticate': 'Bearer'},
    )


def raise_upload_exception(msg: str):
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)
