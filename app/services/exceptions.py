class UserNotFoundException(Exception):
    def __init__(self, username: str):
        self.username = username
        super().__init__(f"User '{username}' not found.")

class DuplicateUserException(Exception):
    def __init__(self, field: str, value: str):
        self.field = field
        self.value = value
        super().__init__(f"User with {field} '{value}' already exists.")

class UnauthorizedActionException(Exception):
    def __init__(self, message: str):
        super().__init__(message)
