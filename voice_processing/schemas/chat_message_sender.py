from enum import StrEnum


class ChatMessageSender(StrEnum):
    """Sender of a given message."""

    USER = "USER"
    AI = "AI"
