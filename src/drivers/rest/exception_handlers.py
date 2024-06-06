from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from src.use_cases.exceptions import (
    NotARefreshTokenError,
    UserIsBlockedError,
    UserNotFoundError,
    PasswordDoesNotMatchError,
    TokenIsBlacklistedError,
    EmptyUpdateDataError,
    MethodNotAllowedError, InvalidTokenError
)
from src.adapters.exceptions import (
    DatabaseError,
    ImagesBucketError,
    FileSizeError,
    NoFileContentError,
    InvalidFileTypeError, InvalidIdError, NonExistSortKeyError
)


def exception_container(app: FastAPI) -> None:
    @app.exception_handler(NotARefreshTokenError)
    async def not_a_refresh_token_exception_handler(
            request: Request, exc: NotARefreshTokenError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED, content={"message": str(exc)}
        )

    @app.exception_handler(UserIsBlockedError)
    async def user_is_blocked_exception_handler(
            request: Request, exc: UserIsBlockedError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"message": str(exc)},
        )

    @app.exception_handler(UserNotFoundError)
    async def user_not_found_exception_handler(
            request: Request, exc: UserNotFoundError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": str(exc)},
        )

    @app.exception_handler(TokenIsBlacklistedError)
    async def token_is_blacklisted_exception_handler(
            request: Request, exc: TokenIsBlacklistedError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": str(exc)},
        )

    @app.exception_handler(PasswordDoesNotMatchError)
    async def password_does_not_match_exception_handler(
            request: Request, exc: PasswordDoesNotMatchError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"message": "Something went wrong. Please try again"},
        )

    @app.exception_handler(EmptyUpdateDataError)
    async def empty_update_data_exception_handler(
            request: Request, exc: EmptyUpdateDataError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": str(exc)},
        )

    @app.exception_handler(MethodNotAllowedError)
    async def method_not_allowed_exception_handler(
            request: Request, exc: MethodNotAllowedError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
            content={"message": str(exc)},
        )

    @app.exception_handler(DatabaseError)
    async def external_exception_handler(
            request: Request, exc: DatabaseError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": str(exc)},
        )

    @app.exception_handler(InvalidTokenError)
    async def invalid_token_exception_handler(
            request: Request, exc: InvalidTokenError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"message": str(exc)},
        )

    @app.exception_handler(InvalidIdError)
    async def invalid_id_exception_handler(
            request: Request, exc: InvalidIdError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": str(exc)},
        )

    @app.exception_handler(NonExistSortKeyError)
    async def non_exist_sort_field_exception_handler(
            request: Request, exc: NonExistSortKeyError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": str(exc)}
        )
