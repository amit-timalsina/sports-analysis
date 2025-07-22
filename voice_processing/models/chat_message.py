import uuid
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Boolean, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import ProductionBase
from voice_processing.schemas.chat_message_sender import ChatMessageSender

if TYPE_CHECKING:
    from voice_processing.models.conversation import Conversation


class ChatMessage(ProductionBase):
    """
    Represents a chat message in the application.

    Every chat message is associated with a conversation.
    """

    __tablename__ = "chat_messages"

    sender: Mapped[ChatMessageSender] = mapped_column(
        Enum(ChatMessageSender),
        nullable=False,
    )
    user_message: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )
    ai_extraction: Mapped[dict | None] = mapped_column(  # type: ignore[type-arg]
        JSON,
        nullable=True,
    )
    is_read: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    is_completed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # Every message is associated with a conversation.
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    conversation: Mapped["Conversation"] = relationship(
        back_populates="chat_messages",
        lazy="selectin",
    )

    # Every messaage can have only one parent message.
    # This is used for thread replies.
    parent_message_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("chat_messages.id"),
        nullable=True,
        index=True,
    )
    parent_message: Mapped["ChatMessage"] = relationship(
        back_populates="replies",
        remote_side="ChatMessage.id",
    )

    # Every message can have multiple replies.
    replies: Mapped[list["ChatMessage"]] = relationship(
        back_populates="parent_message",
    )
