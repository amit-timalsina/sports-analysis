from collections.abc import AsyncGenerator

import svcs

from common.repositories.crud_repository import CRUDRepository
from database.session import AsyncSession
from voice_processing.exceptions.conversation_errors import (
    ConversationCreationError,
    ConversationNotFoundError,
)
from voice_processing.models.conversation import Conversation
from voice_processing.schemas.conversation import (
    ConversationCreate,
    ConversationRead,
    ConversationUpdate,
)


class ConversationRepository(
    CRUDRepository[
        Conversation,
        ConversationCreate,
        ConversationRead,
        ConversationUpdate,
    ],
):
    """Repository for managing conversation-related database operations."""

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize the conversation repository.

        Args:
        ----
            session: The database session.

        """
        super().__init__(
            model=Conversation,
            create_schema=ConversationCreate,
            read_schema=ConversationRead,
            update_schema=ConversationUpdate,
            session=session,
            not_found_exception=ConversationNotFoundError,
            creation_exception=ConversationCreationError,
        )

    @classmethod
    async def get_as_dependency(
        cls,
        services: svcs.Container,
    ) -> AsyncGenerator["ConversationRepository", None]:
        """
        Get the conversation repository as a dependency.

        Args:
        ----
            services: The service container used for dependency injection.

        Yields:
        ------
            ConversationRepository: The conversation repository.

        """
        session = await services.aget(AsyncSession)
        yield ConversationRepository(session)
