"""Conversation repositories for data access layer."""

from collections.abc import AsyncGenerator

import svcs
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import UnaryExpression

from common.repositories.crud_repository import CRUDRepository
from voice_processing.exceptions import (
    ConversationCreationError,
    ConversationNotFoundError,
    MessageCreationError,
    QuestionContextCreationError,
)
from voice_processing.models.conversation import (
    Conversation,
    ConversationAnalytics,
    ConversationMessage,
    ConversationState,
    ConversationTurn,
    QuestionContext,
)
from voice_processing.schemas.conversation import (
    ConversationAnalyticsCreate,
    ConversationAnalyticsRead,
    ConversationAnalyticsUpdate,
    ConversationCreate,
    ConversationMessageCreate,
    ConversationMessageRead,
    ConversationRead,
    ConversationTurnCreate,
    ConversationTurnRead,
    ConversationUpdate,
    QuestionContextCreate,
    QuestionContextRead,
    QuestionContextUpdate,
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
        """Initialize the conversation repository."""
        super().__init__(
            model=Conversation,
            create_schema=ConversationCreate,
            read_schema=ConversationRead,
            update_schema=ConversationUpdate,
            session=session,
            not_found_exception=ConversationNotFoundError,
            creation_exception=ConversationCreationError,
            user_filter=self._user_filter,
        )

    def _user_filter(self, user):
        """Filter conversations by user."""
        if user:
            return Conversation.user_id == user.id
        return False

    async def read_by_session_id(self, session_id: str, current_user=None) -> ConversationRead:
        """Get conversation by session ID."""
        return await self.read_by_filter(
            Conversation.session_id == session_id,
            current_user,
        )

    async def read_active_conversations(
        self,
        current_user=None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[ConversationRead]:
        """Get active (non-completed) conversations."""
        return await self.read_multi_by_filter(
            Conversation.state.in_(
                [
                    ConversationState.STARTED,
                    ConversationState.COLLECTING_DATA,
                    ConversationState.ASKING_FOLLOWUP,
                    ConversationState.VALIDATING_DATA,
                ],
            ),
            current_user=current_user,
            offset=offset,
            limit=limit,
        )

    async def read_by_activity_type(
        self,
        activity_type: str,
        current_user=None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[ConversationRead]:
        """Get conversations by activity type."""
        return await self.read_multi_by_filter(
            Conversation.activity_type == activity_type,
            current_user=current_user,
            offset=offset,
            limit=limit,
        )

    @classmethod
    async def get_as_dependency(
        cls,
        services: svcs.Container,
    ) -> AsyncGenerator["ConversationRepository", None]:
        """Get the conversation repository as a dependency."""
        session = await services.aget(AsyncSession)
        yield ConversationRepository(session)


class ConversationMessageRepository(
    CRUDRepository[
        ConversationMessage,
        ConversationMessageCreate,
        ConversationMessageRead,
        ConversationMessageCreate,  # No separate update schema needed
    ],
):
    """Repository for managing conversation message operations."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the conversation message repository."""
        super().__init__(
            model=ConversationMessage,
            create_schema=ConversationMessageCreate,
            read_schema=ConversationMessageRead,
            update_schema=ConversationMessageCreate,
            session=session,
            not_found_exception=ConversationNotFoundError,
            creation_exception=MessageCreationError,
            user_filter=self._user_filter,
        )

    def _user_filter(self, user):
        """Filter messages by user through conversation."""
        if user:
            return ConversationMessage.conversation_id.in_(
                select(Conversation.id).filter(Conversation.user_id == user.id),
            )
        return False

    async def read_by_conversation(
        self,
        conversation_id: int,
        current_user=None,
        order_by: UnaryExpression | None = None,
    ) -> list[ConversationMessageRead]:
        """Get all messages for a conversation."""
        if order_by is None:
            order_by = ConversationMessage.sequence_number.asc()

        return await self.read_multi_by_filter(
            ConversationMessage.conversation_id == conversation_id,
            current_user=current_user,
            order_by=order_by,
        )

    async def read_by_turn(
        self,
        turn_id: int,
        current_user=None,
    ) -> list[ConversationMessageRead]:
        """Get all messages for a specific turn."""
        return await self.read_multi_by_filter(
            ConversationMessage.turn_id == turn_id,
            current_user=current_user,
            order_by=ConversationMessage.sequence_number.asc(),
        )

    @classmethod
    async def get_as_dependency(
        cls,
        services: svcs.Container,
    ) -> AsyncGenerator["ConversationMessageRepository", None]:
        """Get the conversation message repository as a dependency."""
        session = await services.aget(AsyncSession)
        yield ConversationMessageRepository(session)


class ConversationTurnRepository(
    CRUDRepository[
        ConversationTurn,
        ConversationTurnCreate,
        ConversationTurnRead,
        ConversationTurnCreate,  # No separate update schema needed
    ],
):
    """Repository for managing conversation turn operations."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the conversation turn repository."""
        super().__init__(
            model=ConversationTurn,
            create_schema=ConversationTurnCreate,
            read_schema=ConversationTurnRead,
            update_schema=ConversationTurnCreate,
            session=session,
            not_found_exception=ConversationNotFoundError,
            creation_exception=ConversationCreationError,
            user_filter=self._user_filter,
        )

    def _user_filter(self, user):
        """Filter turns by user through conversation."""
        if user:
            return ConversationTurn.conversation_id.in_(
                select(Conversation.id).filter(Conversation.user_id == user.id),
            )
        return False

    async def read_by_conversation(
        self,
        conversation_id: int,
        current_user=None,
    ) -> list[ConversationTurnRead]:
        """Get all turns for a conversation."""
        return await self.read_multi_by_filter(
            ConversationTurn.conversation_id == conversation_id,
            current_user=current_user,
            order_by=ConversationTurn.turn_number.asc(),
        )

    async def get_latest_turn(
        self,
        conversation_id: int,
        current_user=None,
    ) -> ConversationTurnRead | None:
        """Get the latest turn for a conversation."""
        session = await self.get_session()
        result = await session.execute(
            select(ConversationTurn)
            .filter(ConversationTurn.conversation_id == conversation_id)
            .filter(self.user_filter(current_user))
            .order_by(ConversationTurn.turn_number.desc())
            .limit(1),
        )
        turn = result.scalar_one_or_none()
        return self._to_read_schema(turn) if turn else None

    @classmethod
    async def get_as_dependency(
        cls,
        services: svcs.Container,
    ) -> AsyncGenerator["ConversationTurnRepository", None]:
        """Get the conversation turn repository as a dependency."""
        session = await services.aget(AsyncSession)
        yield ConversationTurnRepository(session)


class QuestionContextRepository(
    CRUDRepository[
        QuestionContext,
        QuestionContextCreate,
        QuestionContextRead,
        QuestionContextUpdate,
    ],
):
    """Repository for managing question context operations."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the question context repository."""
        super().__init__(
            model=QuestionContext,
            create_schema=QuestionContextCreate,
            read_schema=QuestionContextRead,
            update_schema=QuestionContextUpdate,
            session=session,
            not_found_exception=ConversationNotFoundError,
            creation_exception=QuestionContextCreationError,
            user_filter=self._user_filter,
        )

    def _user_filter(self, user):
        """Filter question contexts by user through conversation."""
        if user:
            return QuestionContext.conversation_id.in_(
                select(Conversation.id).filter(Conversation.user_id == user.id),
            )
        return False

    async def read_by_conversation(
        self,
        conversation_id: int,
        current_user=None,
    ) -> list[QuestionContextRead]:
        """Get all question contexts for a conversation."""
        return await self.read_multi_by_filter(
            QuestionContext.conversation_id == conversation_id,
            current_user=current_user,
            order_by=QuestionContext.asked_at_turn.asc(),
        )

    async def read_pending_questions(
        self,
        conversation_id: int,
        current_user=None,
    ) -> list[QuestionContextRead]:
        """Get pending questions for a conversation."""
        from voice_processing.models.conversation import ResolutionStatus

        return await self.read_multi_by_filter(
            (QuestionContext.conversation_id == conversation_id)
            & (QuestionContext.resolution_status == ResolutionStatus.PENDING),
            current_user=current_user,
        )

    @classmethod
    async def get_as_dependency(
        cls,
        services: svcs.Container,
    ) -> AsyncGenerator["QuestionContextRepository", None]:
        """Get the question context repository as a dependency."""
        session = await services.aget(AsyncSession)
        yield QuestionContextRepository(session)


class ConversationAnalyticsRepository(
    CRUDRepository[
        ConversationAnalytics,
        ConversationAnalyticsCreate,
        ConversationAnalyticsRead,
        ConversationAnalyticsUpdate,
    ],
):
    """Repository for managing conversation analytics operations."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the conversation analytics repository."""
        super().__init__(
            model=ConversationAnalytics,
            create_schema=ConversationAnalyticsCreate,
            read_schema=ConversationAnalyticsRead,
            update_schema=ConversationAnalyticsUpdate,
            session=session,
            not_found_exception=ConversationNotFoundError,
            creation_exception=ConversationCreationError,
            user_filter=self._user_filter,
        )

    def _user_filter(self, user):
        """Filter analytics by user."""
        if user:
            return ConversationAnalytics.user_id == user.id
        return ConversationAnalytics.user_id.is_(None)  # Global analytics if no user

    async def read_global_analytics(
        self,
        start_date: str | None = None,
        end_date: str | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[ConversationAnalyticsRead]:
        """Get global analytics (user_id is null)."""
        filter_condition = ConversationAnalytics.user_id.is_(None)

        if start_date:
            filter_condition &= ConversationAnalytics.date >= start_date
        if end_date:
            filter_condition &= ConversationAnalytics.date <= end_date

        return await self.read_multi_by_filter(
            filter_condition,
            offset=offset,
            limit=limit,
            order_by=ConversationAnalytics.date.desc(),
        )

    @classmethod
    async def get_as_dependency(
        cls,
        services: svcs.Container,
    ) -> AsyncGenerator["ConversationAnalyticsRepository", None]:
        """Get the conversation analytics repository as a dependency."""
        session = await services.aget(AsyncSession)
        yield ConversationAnalyticsRepository(session)
