from typing import TYPE_CHECKING

from sqlalchemy import Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from common.mixins.relationship_factories import user_relationship_factory
from database.base import ProductionBase
from fitness_tracking.schemas.enums.activity_type import ActivityType

if TYPE_CHECKING:
    from common.models.activity import ActivityEntry
    from voice_processing.models.chat_message import ChatMessage


class Conversation(
    ProductionBase,
    user_relationship_factory(  # type: ignore[misc]
        back_populates="conversations",
        ondelete="SET NULL",
        nullable=True,
    ),
):
    """
    Represents a conversation in the application.

    A conversation is a collection of chat messages between Application and User.

    """

    __tablename__ = "conversations"
    activity_type: Mapped[ActivityType] = mapped_column(
        Enum(ActivityType),
        nullable=False,
    )
    chat_messages: Mapped[list["ChatMessage"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="ChatMessage.created_at",
        lazy="selectin",
    )
    activity_entries: Mapped[list["ActivityEntry"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="ActivityEntry.created_at",
        lazy="selectin",
    )

    # TODO (Amit): Add computed fields like:
    #  total message count,
    #  token incoming message character count
    #  token outgoing message character count
    # Note: Not sure how important character count is. Token count is more important.
