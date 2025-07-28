"""Conversation routers for voice processing API endpoints."""

from uuid import UUID

import svcs
from fastapi import APIRouter

# Note: These imports would need to be updated based on your auth system
# from auth.dependencies.security import get_current_user
# from auth.schemas.user import User as UserGet
from voice_processing.exceptions import (
    ConversationCreationError,
    ConversationNotFoundError,
    MessageCreationError,
    QuestionContextCreationError,
)
from voice_processing.repositories import (
    ConversationAnalyticsRepository,
    ConversationRepository,
    QuestionContextRepository,
)
from voice_processing.repositories.chat_message_repository import (
    ConversationMessageRepository,
)
from voice_processing.schemas import (
    ConversationAnalyticsCreate,
    ConversationAnalyticsRead,
    ConversationCreate,
    ConversationMessageCreate,
    ConversationMessageRead,
    ConversationRead,
    ConversationUpdate,
    QuestionContextCreate,
    QuestionContextRead,
    QuestionContextUpdate,
)

# Initialize routers
conversation_router = APIRouter(prefix="/conversations", tags=["conversations"])
message_router = APIRouter(prefix="/messages", tags=["conversation-messages"])
question_router = APIRouter(prefix="/questions", tags=["question-contexts"])
analytics_router = APIRouter(prefix="/analytics", tags=["conversation-analytics"])


# Conversation Endpoints
@conversation_router.post("", response_model=ConversationRead)
async def create_conversation(
    conversation: ConversationCreate,
    dep_container: svcs.fastapi.DepContainer,
    # current_user: Annotated[UserGet, Depends(get_current_user)],
) -> ConversationRead:
    """Create a new conversation."""
    repository = await dep_container.aget(ConversationRepository)

    try:
        return await repository.create(conversation)  # , current_user)
    except ConversationCreationError as e:
        raise e.to_http_exception() from None


@conversation_router.get("", response_model=list[ConversationRead])
async def read_conversations(
    dep_container: svcs.fastapi.DepContainer,
    # current_user: Annotated[UserGet, Depends(get_current_user)],
    offset: int = 0,
    limit: int = 100,
) -> list[ConversationRead]:
    """Get conversations."""
    repository = await dep_container.aget(ConversationRepository)
    return await repository.read_multi(offset=offset, limit=limit)  # current_user=current_user


@conversation_router.get("/active", response_model=list[ConversationRead])
async def read_active_conversations(
    dep_container: svcs.fastapi.DepContainer,
    # current_user: Annotated[UserGet, Depends(get_current_user)],
    offset: int = 0,
    limit: int = 100,
) -> list[ConversationRead]:
    """Get active conversations."""
    repository = await dep_container.aget(ConversationRepository)
    return await repository.read_active_conversations(
        offset=offset,
        limit=limit,
    )  # current_user=current_user


@conversation_router.get("/by-session/{session_id}", response_model=ConversationRead)
async def read_conversation_by_session(
    session_id: str,
    dep_container: svcs.fastapi.DepContainer,
    # current_user: Annotated[UserGet, Depends(get_current_user)],
) -> ConversationRead:
    """Get conversation by session ID."""
    repository = await dep_container.aget(ConversationRepository)

    try:
        return await repository.read_by_session_id(session_id)  # , current_user)
    except ConversationNotFoundError as e:
        raise e.to_http_exception() from None


@conversation_router.get("/{conversation_id}", response_model=ConversationRead)
async def read_conversation(
    conversation_id: UUID,
    dep_container: svcs.fastapi.DepContainer,
    # current_user: Annotated[UserGet, Depends(get_current_user)],
) -> ConversationRead:
    """Get a specific conversation."""
    repository = await dep_container.aget(ConversationRepository)

    try:
        return await repository.read(conversation_id)  # , current_user)
    except ConversationNotFoundError as e:
        raise e.to_http_exception() from None


@conversation_router.put("/{conversation_id}", response_model=ConversationRead)
async def update_conversation(
    conversation_id: UUID,
    conversation_update: ConversationUpdate,
    dep_container: svcs.fastapi.DepContainer,
    # current_user: Annotated[UserGet, Depends(get_current_user)],
) -> ConversationRead:
    """Update a conversation."""
    repository = await dep_container.aget(ConversationRepository)

    try:
        return await repository.update(conversation_id, conversation_update)  # , current_user)
    except ConversationNotFoundError as e:
        raise e.to_http_exception() from None


# Message Endpoints
@message_router.post("", response_model=ConversationMessageRead)
async def create_message(
    message: ConversationMessageCreate,
    dep_container: svcs.fastapi.DepContainer,
    # current_user: Annotated[UserGet, Depends(get_current_user)],
) -> ConversationMessageRead:
    """Create a new conversation message."""
    repository = await dep_container.aget(ConversationMessageRepository)

    try:
        return await repository.create(message)  # , current_user)
    except MessageCreationError as e:
        raise e.to_http_exception() from None


@message_router.get("/conversation/{conversation_id}", response_model=list[ConversationMessageRead])
async def read_messages_by_conversation(
    conversation_id: int,
    dep_container: svcs.fastapi.DepContainer,
    # current_user: Annotated[UserGet, Depends(get_current_user)],
) -> list[ConversationMessageRead]:
    """Get all messages for a conversation."""
    repository = await dep_container.aget(ConversationMessageRepository)
    return await repository.read_by_conversation(conversation_id)  # , current_user)


@message_router.get("/turn/{turn_id}", response_model=list[ConversationMessageRead])
async def read_messages_by_turn(
    turn_id: int,
    dep_container: svcs.fastapi.DepContainer,
    # current_user: Annotated[UserGet, Depends(get_current_user)],
) -> list[ConversationMessageRead]:
    """Get all messages for a specific turn."""
    repository = await dep_container.aget(ConversationMessageRepository)
    return await repository.read_by_turn(turn_id)  # , current_user)


# Question Context Endpoints
@question_router.post("", response_model=QuestionContextRead)
async def create_question_context(
    question: QuestionContextCreate,
    dep_container: svcs.fastapi.DepContainer,
    # current_user: Annotated[UserGet, Depends(get_current_user)],
) -> QuestionContextRead:
    """Create a new question context."""
    repository = await dep_container.aget(QuestionContextRepository)

    try:
        return await repository.create(question)  # , current_user)
    except QuestionContextCreationError as e:
        raise e.to_http_exception() from None


@question_router.get("/conversation/{conversation_id}", response_model=list[QuestionContextRead])
async def read_questions_by_conversation(
    conversation_id: int,
    dep_container: svcs.fastapi.DepContainer,
    # current_user: Annotated[UserGet, Depends(get_current_user)],
) -> list[QuestionContextRead]:
    """Get all question contexts for a conversation."""
    repository = await dep_container.aget(QuestionContextRepository)
    return await repository.read_by_conversation(conversation_id)  # , current_user)


@question_router.get(
    "/conversation/{conversation_id}/pending",
    response_model=list[QuestionContextRead],
)
async def read_pending_questions(
    conversation_id: int,
    dep_container: svcs.fastapi.DepContainer,
    # current_user: Annotated[UserGet, Depends(get_current_user)],
) -> list[QuestionContextRead]:
    """Get pending questions for a conversation."""
    repository = await dep_container.aget(QuestionContextRepository)
    return await repository.read_pending_questions(conversation_id)  # , current_user)


@question_router.put("/{question_id}", response_model=QuestionContextRead)
async def update_question_context(
    question_id: UUID,
    question_update: QuestionContextUpdate,
    dep_container: svcs.fastapi.DepContainer,
    # current_user: Annotated[UserGet, Depends(get_current_user)],
) -> QuestionContextRead:
    """Update a question context."""
    repository = await dep_container.aget(QuestionContextRepository)

    try:
        return await repository.update(question_id, question_update)  # , current_user)
    except ConversationNotFoundError as e:
        raise e.to_http_exception() from None


# Analytics Endpoints
@analytics_router.post("", response_model=ConversationAnalyticsRead)
async def create_analytics(
    analytics: ConversationAnalyticsCreate,
    dep_container: svcs.fastapi.DepContainer,
    # current_user: Annotated[UserGet, Depends(get_current_user)],
) -> ConversationAnalyticsRead:
    """Create conversation analytics."""
    repository = await dep_container.aget(ConversationAnalyticsRepository)

    try:
        return await repository.create(analytics)  # , current_user)
    except ConversationCreationError as e:
        raise e.to_http_exception() from None


@analytics_router.get("/global", response_model=list[ConversationAnalyticsRead])
async def read_global_analytics(
    dep_container: svcs.fastapi.DepContainer,
    start_date: str | None = None,
    end_date: str | None = None,
    offset: int = 0,
    limit: int = 100,
) -> list[ConversationAnalyticsRead]:
    """Get global conversation analytics."""
    repository = await dep_container.aget(ConversationAnalyticsRepository)
    return await repository.read_global_analytics(
        start_date=start_date,
        end_date=end_date,
        offset=offset,
        limit=limit,
    )
