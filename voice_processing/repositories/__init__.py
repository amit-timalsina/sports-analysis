"""Voice processing repositories for data access."""

from .chat_message_repository import ChatMessageRepository
from .conversation_repository import ConversationRepository

__all__ = (
    "ChatMessageRepository",
    "ConversationRepository",
)
