from fastapi import HTTPException
from starlette import status


class CredentialException(HTTPException):
    def __init__(self, message: str):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=message)


class UploadImageException(HTTPException):
    def __init__(self, message: str):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=message)
