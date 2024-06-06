class ExternalError(Exception):
    pass


class DatabaseError(ExternalError):
    def __init__(self, error: Exception):
        self.error = error

    def __str__(self):
        return str(self.error)


class InvalidIdError(ExternalError):
    def __init__(self, invalid_id: str):
        self.error = invalid_id

    def __str__(self):
        return f'Invalid id provided: {self.error}'


class NonExistSortKeyError(ExternalError):
    def __init__(self, field: str):
        self.error = field

    def __str__(self):
        return f'Sort field {self.error} does not exist'


class ImagesBucketError(ExternalError):
    def __init__(self, error: Exception):
        self.error = error

    def __str__(self):
        return str(self.error)


class NoFileContentError(ExternalError):
    def __str__(self) -> str:
        return 'File is empty or not provided'


class FileSizeError(ExternalError):
    def __init__(self, error: str) -> None:
        self.error = error

    def __str__(self) -> str:
        return f'File size error: {self.error}'


class InvalidFileTypeError(ExternalError):
    def __init__(self, error: str) -> None:
        self.error = error

    def __str__(self) -> str:
        return self.error
