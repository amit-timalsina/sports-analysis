from voice_processing.exceptions.conversation_errors import AppChatError


class ChatMessageNotFoundError(AppChatError):
    """Raised when a chat message is not found in the database."""

    status_code: int = 404
    detail: str = "Not Found. The chat message does not exist."


class ChatMessageCreationError(AppChatError):
    """Raised when a chat message creation fails."""

    status_code: int = 500
    detail: str = "Internal Server Error. Failed to create the chat message."
