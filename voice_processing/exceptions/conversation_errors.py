from common.exceptions.app_error import AppError


class AppChatError(AppError):
    """Base exception for chat-related errors."""

    status_code: int = 400
    detail: str = "Bad Request. Please check your input."


class ConversationNotFoundError(AppChatError):
    """Raised when a conversation is not found in the database."""

    status_code: int = 404
    detail: str = "Not Found. The conversation does not exist."


class ConversationCreationError(AppChatError):
    """Raised when a conversation creation fails."""

    status_code: int = 500
    detail: str = "Internal Server Error. Failed to create the conversation."
