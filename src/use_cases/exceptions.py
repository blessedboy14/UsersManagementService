from uuid import UUID


class UserNotFoundError(Exception):
    def __init__(self, login: str):
        self.login = login

    def __str__(self) -> str:
        return f'User not found for login: {self.login}'


class UserIsBlockedError(Exception):
    def __init__(self, user_id: UUID):
        self.user_id = user_id

    def __str__(self) -> str:
        return f'User is blocked: {self.user_id}'


class PasswordDoesNotMatchError(Exception):
    def __init__(self, user_id: UUID):
        self.user_id = user_id

    def __str__(self) -> str:
        return f'Passwords does not match for user: {self.user_id}'


class TokenIsBlacklistedError(Exception):
    def __str__(self) -> str:
        return "Can't refresh token, current is blacklisted"


class NotARefreshTokenError(Exception):
    def __str__(self) -> str:
        return 'Provided token cannot be determined as refresh'


class EmptyUpdateDataError(Exception):
    def __init__(self, user_id: UUID):
        self.user_id = user_id

    def __str__(self) -> str:
        return f'Empty update data for user: {self.user_id}'


class MethodNotAllowedError(Exception):
    def __init__(self, user_id: UUID):
        self.user_id = user_id

    def __str__(self) -> str:
        return f'Method not allowed for user: {self.user_id}'


class InvalidTokenError(Exception):
    def __str__(self) -> str:
        return 'Invalid access token'
