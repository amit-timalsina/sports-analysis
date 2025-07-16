from common.exceptions.app_error import AppError


class AppAuthenticationError(AppError):
    """Base exception for authentication-related errors."""

    status_code: int = 401
    detail: str = "Unauthorized. Please check your credentials."


class AppAuthorizationError(AppError):
    """Base exception for authorization-related errors."""

    status_code: int = 403
    detail: str = "Forbidden. Please check your permissions."


class UserAlreadyExistsError(AppAuthenticationError):
    """Raised when attempting to create a user with an email that already exists."""

    status_code: int = 409
    detail: str = "Conflict. The user already exists."


class UserNotFoundError(AppAuthenticationError):
    """Raised when a user is not found in the database."""

    status_code: int = 404
    detail: str = "Not Found. The user does not exist."


class UserCreationError(AppAuthenticationError):
    """Raised when a user creation fails."""

    status_code: int = 500
    detail: str = "Internal Server Error. Failed to create the user."
