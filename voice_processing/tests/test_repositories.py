"""Test cases for voice processing repositories."""

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from voice_processing.models.conversation import (
    Conversation,
    ConversationAnalytics,
    ConversationMessage,
    ConversationTurn,
    QuestionContext,
)
from voice_processing.repositories import (
    ConversationAnalyticsRepository,
    ConversationRepository,
    ConversationTurnRepository,
    QuestionContextRepository,
)
from voice_processing.repositories.chat_message_repository import (
    ConversationMessageRepository,
)
from voice_processing.schemas.conversation_detail_enums import (
    ActivityType,
    ConversationStage,
    MessageType,
    QuestionType,
)
from voice_processing.schemas.conversation_enums import ConversationState, ResolutionStatus
from voice_processing.schemas.conversation_old import (
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
    now = datetime.now(UTC)
    return Conversation(
        id=uuid.uuid4(),
        user_id="user123",
        session_id="session123",
        activity_type=ActivityType.FITNESS,
        state=ConversationState.STARTED,
        stage=ConversationStage.INITIAL_INPUT,
        current_data={},
        data_confidence={},
        missing_fields=[],
        validation_errors={},
        pending_questions=[],
        question_attempts={},
        total_turns=0,
        total_messages=0,
        completion_status="incomplete",
        final_data={},
        started_at=now,
        last_activity_at=now,
        completed_at=None,
        total_duration_seconds=None,
        activity_entry_id=None,
        activity_entry_type=None,
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def sample_message():
    """Create a sample conversation message."""
    now = datetime.now(UTC)
    return ConversationMessage(
        id=uuid.uuid4(),
        conversation_id=uuid.uuid4(),
        message_type=MessageType.USER_INPUT,
        sequence_number=1,
        content="Test message",
        turn_id=None,
        parent_message_id=None,
        raw_transcript=None,
        transcript_confidence=None,
        processing_duration=None,
        ai_model_used=None,
        ai_temperature=None,
        ai_tokens_used=None,
        extracted_data={},
        extraction_confidence=None,
        message_timestamp=now,
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def sample_turn():
    """Create a sample conversation turn."""
    now = datetime.now(UTC)
    return ConversationTurn(
        id=uuid.uuid4(),
        conversation_id=uuid.uuid4(),
        turn_number=1,
        data_extracted_this_turn={},
        questions_resolved=[],
        new_questions_raised=[],
        turn_effectiveness_score=None,
        data_completeness_after_turn=None,
        turn_strategy=None,
        turn_started_at=now,
        turn_completed_at=None,
        turn_duration_seconds=None,
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def sample_question_context():
    """Create a sample question context."""
    now = datetime.now(UTC)
    return QuestionContext(
        id=uuid.uuid4(),
        conversation_id=uuid.uuid4(),
        target_field="name",
        question_text="What is your name?",
        question_type=QuestionType.REQUIRED,
        asked_at_turn=1,
        attempts_count=1,
        max_attempts=3,
        resolution_status=ResolutionStatus.PENDING,
        question_strategy="direct",
        context_data={},
        first_asked_at=now,
        resolved_at_turn=None,
        resolved_with_confidence=None,
        final_answer=None,
        resolved_at=None,
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def sample_analytics():
    """Create a sample conversation analytics."""
    now = datetime.now(UTC)
    return ConversationAnalytics(
        id=uuid.uuid4(),
        user_id="user123",
        date=datetime.now(UTC),
        total_conversations=10,
        completed_conversations=8,
        abandoned_conversations=1,
        error_conversations=1,
        average_turns_per_conversation=None,
        average_messages_per_conversation=None,
        average_conversation_duration=None,
        median_conversation_duration=None,
        average_data_quality=None,
        average_efficiency=None,
        average_user_satisfaction=None,
        activity_breakdown={},
        completion_rate_by_activity={},
        most_asked_questions=[],
        most_problematic_fields=[],
        question_success_rates={},
        average_time_per_stage={},
        stage_completion_rates={},
        average_ai_response_time=None,
        ai_model_usage={},
        total_ai_tokens_used=None,
        created_at=now,
        updated_at=now,
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
        activity_type = ActivityType.FITNESS
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
        conversation_id = uuid.uuid4()
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
        turn_id = uuid.uuid4()
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
        conversation_id = uuid.uuid4()
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
        conversation_id = uuid.uuid4()
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
        conversation_id = uuid.uuid4()
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
        conversation_id = uuid.uuid4()
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
