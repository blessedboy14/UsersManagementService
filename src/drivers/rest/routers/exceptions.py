class ModelValidationError(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return f'Model validation error with message: {self.message}'
