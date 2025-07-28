from uuid import UUID

from pydantic import Field, model_validator

from common.schemas.app_base_model import AppBaseModel
from common.schemas.primary_key_base import PrimaryKeyBase
from common.schemas.timestamp_base import TimestampBase
from voice_processing.schemas.chat_message_sender import ChatMessageSender


class ChatMessageBase(AppBaseModel):
    """Represents a chat message in the application."""

    sender: ChatMessageSender = Field(..., description="The sender of the message.")
    conversation_id: UUID = Field(
        ...,
        description="Identifier of the conversation this message belongs to.",
    )
    user_message: str | None = Field(
        default=None,
        description="The message content.",
    )
    # ai_extraction: (
    #     FitnessDataExtraction
    #     | CricketMatchDataExtraction
    #     | CricketCoachingDataExtraction
    #     | RestDayDataExtraction
    # ) = Field(..., description="The AI extraction of the message.")
    ai_extraction: dict | None = Field(
        default=None,
        description="The AI extraction of the message.",
    )
    is_read: bool = Field(..., description="Whether the message has been read.")
    is_completed: bool = Field(..., description="Whether the message has been completed.")
    parent_message_id: UUID | None = Field(
        default=None,
        description="""Identifier of the parent message.
        If this is the first message in the conversation, this will be None.
        Messages from Kniru AI will have this field set to the user's previous message.
        Messages from the user will have this field set to Kniru AI's previous message.

        Edits and Replies will also be maintained using this field.
        For reference, refer to chat/diagrams/chat_message_parent_id.png
        """,
    )

    def mark_as_read(self) -> None:
        """Mark the message as read."""
        self.is_read = True

    def mark_as_completed(self) -> None:
        """Mark the message as completed."""
        self.is_completed = True

    def is_reply(self) -> bool:
        """Check if the message is a reply to another message."""
        return self.parent_message_id is not None

    @model_validator(mode="after")
    def either_user_message_or_ai_extraction(self) -> "ChatMessageBase":
        """Validate the AI extraction."""
        if self.user_message is None and self.ai_extraction is None:
            msg = "Either user_message or ai_extraction must be provided."
            raise ValueError(msg)
        return self


class ChatMessage(PrimaryKeyBase, TimestampBase, ChatMessageBase):
    """Represents a chat message in the application."""

    def __str__(self) -> str:
        """Return a string representation of the message."""
        return (
            f"ChatMessage(id={self.id}, sender={self.sender}, user_message={self.user_message},"
            f" ai_extraction={self.ai_extraction})"
        )
