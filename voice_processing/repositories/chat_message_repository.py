from collections.abc import AsyncGenerator

import svcs

from common.repositories.crud_repository import CRUDRepository
from database.session import AsyncSession
from voice_processing.exceptions.chat_message_errors import (
    ChatMessageCreationError,
    ChatMessageNotFoundError,
)
from voice_processing.models.chat_message import ChatMessage
from voice_processing.schemas.chat_message import ChatMessage as ChatMessageSchema
from voice_processing.schemas.chat_message import ChatMessageBase


class ChatMessageRepository(
    CRUDRepository[
        ChatMessage,
        ChatMessageBase,
        ChatMessageSchema,
        ChatMessageBase,
    ],
):
    """Repository for managing chat message-related database operations."""

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize the chat message repository.

        Args:
        ----
            session: The database session.

        """
        super().__init__(
            model=ChatMessage,
            create_schema=ChatMessageBase,
            read_schema=ChatMessageSchema,
            update_schema=ChatMessageBase,
            session=session,
            not_found_exception=ChatMessageNotFoundError,
            creation_exception=ChatMessageCreationError,
        )

    @classmethod
    async def get_as_dependency(
        cls,
        services: svcs.Container,
    ) -> AsyncGenerator["ChatMessageRepository", None]:
        """
        Get the chat message repository as a dependency.

        Args:
        ----
            services: The service container used for dependency injection.

        Yields:
        ------
            ChatMessageRepository: The chat message repository.

        """
        session = await services.aget(AsyncSession)
        yield ChatMessageRepository(session)
