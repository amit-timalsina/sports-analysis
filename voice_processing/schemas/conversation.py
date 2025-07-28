from pydantic import Field

from common.schemas.app_base_model import AppBaseModel
from common.schemas.primary_key_base import PrimaryKeyBase
from common.schemas.timestamp_base import TimestampBase
from fitness_tracking.schemas.enums.activity_type import ActivityType
from voice_processing.schemas.chat_message import ChatMessage


class ConversationBase(AppBaseModel):
    """Base Schema for all conversations."""


class ConversationUpdate(ConversationBase):
    """An ordered list of messages between AI and a user."""


class ConversationCreate(ConversationBase):
    """An ordered list of messages between AI and a user."""

    activity_type: ActivityType = Field(
        ...,
        description="The type of activity this conversation is about.",
    )

    chat_messages: list[ChatMessage] = Field(
        default_factory=list,
        description="List of messages in the conversation",
    )

    def get_last_message(self) -> ChatMessage | None:
        """Get the last message in the conversation."""
        return self.chat_messages[-1] if self.chat_messages else None

    def get_message_count(self) -> int:
        """Get the total number of messages in the conversation."""
        return len(self.chat_messages)


class ConversationRead(PrimaryKeyBase, TimestampBase, ConversationCreate):
    """An ordered list of messages between AI and a user."""

    def add_message(self, message: ChatMessage) -> None:
        """Add a new message to the conversation."""
        last_message = self.get_last_message()
        if last_message:
            message.parent_message_id = last_message.id
        message.conversation_id = self.id
        self.chat_messages.append(message)
