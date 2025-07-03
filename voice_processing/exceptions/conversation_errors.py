"""Conversation-related exceptions."""

from common.exceptions import AppError


class ConversationError(AppError):
    """Base exception for conversation-related errors."""

    status_code = 500
    detail = "Conversation operation failed"


class ConversationNotFoundError(ConversationError):
    """Exception raised when a conversation is not found."""

    status_code = 404
    detail = "Conversation not found"


class ConversationCreationError(ConversationError):
    """Exception raised when conversation creation fails."""

    status_code = 400
    detail = "Failed to create conversation"


class ConversationUpdateError(ConversationError):
    """Exception raised when conversation update fails."""

    status_code = 400
    detail = "Failed to update conversation"


class MessageCreationError(ConversationError):
    """Exception raised when message creation fails."""

    status_code = 400
    detail = "Failed to create conversation message"


class QuestionContextCreationError(ConversationError):
    """Exception raised when question context creation fails."""

    status_code = 400
    detail = "Failed to create question context"


class InvalidConversationStateError(ConversationError):
    """Exception raised when conversation is in invalid state."""

    status_code = 400
    detail = "Invalid conversation state for this operation"


class MaxTurnsExceededError(ConversationError):
    """Exception raised when conversation exceeds maximum allowed turns."""

    status_code = 400
    detail = "Maximum conversation turns exceeded"
