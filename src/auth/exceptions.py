from fastapi import HTTPException, status


class ModelValidationException(HTTPException):
    def __init__(self, message: str) -> None:
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


class NotFoundException(HTTPException):
    def __init__(self, message: str) -> None:
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=message)


class CreateUserException(HTTPException):
    def __init__(self, username: str, reason: str) -> None:
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=reason)


class LoginUserException(HTTPException):
    def __init__(self, username: str, reason: str) -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f'reason: {reason}, username: {username}',
        )


class TokenException(HTTPException):
    def __init__(self, exc_status: int, reason: str) -> None:
        super().__init__(status_code=exc_status, detail=reason)


class RefreshTokenException(TokenException):
    def __init__(self, exc_status: int, reason: str, token: str) -> None:
        super().__init__(exc_status, f'{reason}; token: {token}')
