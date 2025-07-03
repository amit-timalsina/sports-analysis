"""Test cases for voice processing repositories."""

import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from voice_processing.models.conversation import (
    Conversation,
    ConversationAnalytics,
    ConversationMessage,
    ConversationState,
    ConversationTurn,
    QuestionContext,
    ResolutionStatus,
)
from voice_processing.repositories import (
    ConversationAnalyticsRepository,
    ConversationMessageRepository,
    ConversationRepository,
    ConversationTurnRepository,
    QuestionContextRepository,
)
from voice_processing.schemas.conversation import (
    ConversationAnalyticsRead,
    ConversationMessageRead,
    ConversationRead,
    ConversationTurnRead,
    QuestionContextRead,
)


@pytest.fixture
def mock_session():
    """Create a mock async session."""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def mock_user():
    """Create a mock user."""
    user = MagicMock()
    user.id = "user123"
    return user


@pytest.fixture
def conversation_repository(mock_session):
    """Create a conversation repository instance."""
    return ConversationRepository(mock_session)


@pytest.fixture
def message_repository(mock_session):
    """Create a conversation message repository instance."""
    return ConversationMessageRepository(mock_session)


@pytest.fixture
def turn_repository(mock_session):
    """Create a conversation turn repository instance."""
    return ConversationTurnRepository(mock_session)


@pytest.fixture
def question_context_repository(mock_session):
    """Create a question context repository instance."""
    return QuestionContextRepository(mock_session)


@pytest.fixture
def analytics_repository(mock_session):
    """Create a conversation analytics repository instance."""
    return ConversationAnalyticsRepository(mock_session)


@pytest.fixture
def sample_conversation():
    """Create a sample conversation."""
    return Conversation(
        id=uuid.uuid4(),
        user_id="user123",
        session_id="session123",
        activity_type="fitness",
        state=ConversationState.STARTED,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


@pytest.fixture
def sample_message():
    """Create a sample conversation message."""
    return ConversationMessage(
        id=uuid.uuid4(),
        conversation_id=1,
        turn_id=1,
        role="user",
        content="Test message",
        sequence_number=1,
        timestamp=datetime.utcnow(),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


@pytest.fixture
def sample_turn():
    """Create a sample conversation turn."""
    return ConversationTurn(
        id=uuid.uuid4(),
        conversation_id=1,
        turn_number=1,
        state=ConversationState.STARTED,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


@pytest.fixture
def sample_question_context():
    """Create a sample question context."""
    return QuestionContext(
        id=uuid.uuid4(),
        conversation_id=1,
        question="What is your name?",
        context_type="personal",
        asked_at_turn=1,
        resolution_status=ResolutionStatus.PENDING,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


@pytest.fixture
def sample_analytics():
    """Create a sample conversation analytics."""
    return ConversationAnalytics(
        id=uuid.uuid4(),
        user_id="user123",
        date="2024-01-01",
        total_conversations=10,
        completed_conversations=8,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


class TestConversationRepository:
    """Test cases for ConversationRepository."""

    @pytest.mark.asyncio
    async def test_read_by_session_id(
        self,
        conversation_repository,
        mock_session,
        sample_conversation,
        mock_user,
    ):
        """Test reading conversation by session ID."""
        # Arrange
        session_id = "session123"

        # Mock the read_by_filter method
        with patch.object(
            conversation_repository,
            "read_by_filter",
            return_value=ConversationRead.model_validate(sample_conversation.__dict__),
        ) as mock_read:
            # Act
            result = await conversation_repository.read_by_session_id(
                session_id,
                current_user=mock_user,
            )

            # Assert
            assert result.session_id == session_id
            mock_read.assert_called_once()

    @pytest.mark.asyncio
    async def test_read_active_conversations(
        self,
        conversation_repository,
        mock_session,
        sample_conversation,
        mock_user,
    ):
        """Test reading active conversations."""
        # Arrange
        conversations = [sample_conversation]

        # Mock the read_multi_by_filter method
        with patch.object(
            conversation_repository,
            "read_multi_by_filter",
            return_value=[ConversationRead.model_validate(sample_conversation.__dict__)],
        ) as mock_read:
            # Act
            result = await conversation_repository.read_active_conversations(
                current_user=mock_user,
                offset=0,
                limit=100,
            )

            # Assert
            assert len(result) == 1
            mock_read.assert_called_once()

    @pytest.mark.asyncio
    async def test_read_by_activity_type(
        self,
        conversation_repository,
        mock_session,
        sample_conversation,
        mock_user,
    ):
        """Test reading conversations by activity type."""
        # Arrange
        activity_type = "fitness"
        conversations = [sample_conversation]

        # Mock the read_multi_by_filter method
        with patch.object(
            conversation_repository,
            "read_multi_by_filter",
            return_value=[ConversationRead.model_validate(sample_conversation.__dict__)],
        ) as mock_read:
            # Act
            result = await conversation_repository.read_by_activity_type(
                activity_type,
                current_user=mock_user,
                offset=0,
                limit=100,
            )

            # Assert
            assert len(result) == 1
            assert result[0].activity_type == activity_type
            mock_read.assert_called_once()


class TestConversationMessageRepository:
    """Test cases for ConversationMessageRepository."""

    @pytest.mark.asyncio
    async def test_read_by_conversation(
        self,
        message_repository,
        mock_session,
        sample_message,
        mock_user,
    ):
        """Test reading messages by conversation ID."""
        # Arrange
        conversation_id = 1
        messages = [sample_message]

        # Mock the read_multi_by_filter method
        with patch.object(
            message_repository,
            "read_multi_by_filter",
            return_value=[ConversationMessageRead.model_validate(sample_message.__dict__)],
        ) as mock_read:
            # Act
            result = await message_repository.read_by_conversation(
                conversation_id,
                current_user=mock_user,
            )

            # Assert
            assert len(result) == 1
            mock_read.assert_called_once()

    @pytest.mark.asyncio
    async def test_read_by_turn(
        self,
        message_repository,
        mock_session,
        sample_message,
        mock_user,
    ):
        """Test reading messages by turn ID."""
        # Arrange
        turn_id = 1
        messages = [sample_message]

        # Mock the read_multi_by_filter method
        with patch.object(
            message_repository,
            "read_multi_by_filter",
            return_value=[ConversationMessageRead.model_validate(sample_message.__dict__)],
        ) as mock_read:
            # Act
            result = await message_repository.read_by_turn(
                turn_id,
                current_user=mock_user,
            )

            # Assert
            assert len(result) == 1
            mock_read.assert_called_once()


class TestConversationTurnRepository:
    """Test cases for ConversationTurnRepository."""

    @pytest.mark.asyncio
    async def test_read_by_conversation(
        self,
        turn_repository,
        mock_session,
        sample_turn,
        mock_user,
    ):
        """Test reading turns by conversation ID."""
        # Arrange
        conversation_id = 1
        turns = [sample_turn]

        # Mock the read_multi_by_filter method
        with patch.object(
            turn_repository,
            "read_multi_by_filter",
            return_value=[ConversationTurnRead.model_validate(sample_turn.__dict__)],
        ) as mock_read:
            # Act
            result = await turn_repository.read_by_conversation(
                conversation_id,
                current_user=mock_user,
            )

            # Assert
            assert len(result) == 1
            mock_read.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_latest_turn(
        self,
        turn_repository,
        mock_session,
        sample_turn,
        mock_user,
    ):
        """Test getting the latest turn for a conversation."""
        # Arrange
        conversation_id = 1
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_turn
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Mock _to_read_schema
        with patch.object(
            turn_repository,
            "_to_read_schema",
            return_value=ConversationTurnRead.model_validate(sample_turn.__dict__),
        ):
            # Act
            result = await turn_repository.get_latest_turn(
                conversation_id,
                current_user=mock_user,
            )

            # Assert
            assert result is not None
            assert result.turn_number == 1
            mock_session.execute.assert_called_once()


class TestQuestionContextRepository:
    """Test cases for QuestionContextRepository."""

    @pytest.mark.asyncio
    async def test_read_by_conversation(
        self,
        question_context_repository,
        mock_session,
        sample_question_context,
        mock_user,
    ):
        """Test reading question contexts by conversation ID."""
        # Arrange
        conversation_id = 1
        contexts = [sample_question_context]

        # Mock the read_multi_by_filter method
        with patch.object(
            question_context_repository,
            "read_multi_by_filter",
            return_value=[QuestionContextRead.model_validate(sample_question_context.__dict__)],
        ) as mock_read:
            # Act
            result = await question_context_repository.read_by_conversation(
                conversation_id,
                current_user=mock_user,
            )

            # Assert
            assert len(result) == 1
            mock_read.assert_called_once()

    @pytest.mark.asyncio
    async def test_read_pending_questions(
        self,
        question_context_repository,
        mock_session,
        sample_question_context,
        mock_user,
    ):
        """Test reading pending questions for a conversation."""
        # Arrange
        conversation_id = 1
        contexts = [sample_question_context]

        # Mock the read_multi_by_filter method
        with patch.object(
            question_context_repository,
            "read_multi_by_filter",
            return_value=[QuestionContextRead.model_validate(sample_question_context.__dict__)],
        ) as mock_read:
            # Act
            result = await question_context_repository.read_pending_questions(
                conversation_id,
                current_user=mock_user,
            )

            # Assert
            assert len(result) == 1
            mock_read.assert_called_once()


class TestConversationAnalyticsRepository:
    """Test cases for ConversationAnalyticsRepository."""

    @pytest.mark.asyncio
    async def test_read_global_analytics(
        self,
        analytics_repository,
        mock_session,
        sample_analytics,
    ):
        """Test reading global analytics."""
        # Arrange
        analytics = [sample_analytics]

        # Mock the read_multi_by_filter method
        with patch.object(
            analytics_repository,
            "read_multi_by_filter",
            return_value=[ConversationAnalyticsRead.model_validate(sample_analytics.__dict__)],
        ) as mock_read:
            # Act
            result = await analytics_repository.read_global_analytics(
                start_date="2024-01-01",
                end_date="2024-01-31",
                offset=0,
                limit=100,
            )

            # Assert
            assert len(result) == 1
            mock_read.assert_called_once()

    @pytest.mark.asyncio
    async def test_user_filter_with_user(self, analytics_repository, mock_user):
        """Test user filter with a user."""
        # Act
        filter_result = analytics_repository._user_filter(mock_user)

        # Assert
        # The filter should return a SQLAlchemy expression
        assert filter_result is not None

    @pytest.mark.asyncio
    async def test_user_filter_without_user(self, analytics_repository):
        """Test user filter without a user."""
        # Act
        filter_result = analytics_repository._user_filter(None)

        # Assert
        # The filter should return an expression for null user_id
        assert filter_result is not None
