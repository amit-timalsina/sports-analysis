"""Audio management routes."""

import logging
from typing import Annotated
from uuid import UUID

import svcs
from fastapi import APIRouter, Depends

from auth.dependencies.security import get_current_user
from auth.schemas.user import User
from common.config.settings import settings
from fitness_tracking.schemas.enums.activity_type import ActivityType
from voice_processing.exceptions.chat_message_errors import (
    ChatMessageCreationError,
    ChatMessageNotFoundError,
)
from voice_processing.exceptions.conversation_errors import ConversationNotFoundError
from voice_processing.repositories.chat_message_repository import ChatMessageRepository
from voice_processing.repositories.conversation_repository import ConversationRepository
from voice_processing.schemas.chat_message import ChatMessage, ChatMessageBase
from voice_processing.schemas.chat_message_sender import ChatMessageSender
from voice_processing.services.ai_service import AIService
from voice_processing.services.openai_service import OpenAIService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/messages", tags=["conversation-messages"])


@router.post("", response_model=ChatMessage)
async def create_message(
    message: ChatMessageBase,
    _: Annotated[User, Depends(get_current_user)],
    dep_container: svcs.fastapi.DepContainer,
) -> ChatMessage:
    """Create a new message."""
    chat_message_repository = await dep_container.aget(ChatMessageRepository)
    try:
        return await chat_message_repository.create(message)
    except ChatMessageCreationError as e:
        logger.exception("Failed to create message")
        raise e.to_http_exception() from None


@router.post("/{message_id}/reply", response_model=ChatMessage)
async def reply_to_message(
    message_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    dep_container: svcs.fastapi.DepContainer,
) -> ChatMessage:
    """Reply to a message by ai."""
    conversation_message_repository = await dep_container.aget(ChatMessageRepository)
    try:
        user_message = await conversation_message_repository.read(message_id)
    except ChatMessageNotFoundError as e:
        raise e.to_http_exception() from None

    conversation_repository = await dep_container.aget(ConversationRepository)
    try:
        conversation = await conversation_repository.read(
            user_message.conversation_id,
            current_user=current_user,
        )
    except ConversationNotFoundError as e:
        raise e.to_http_exception() from None

    openai_service = await dep_container.aget(OpenAIService)
    activity_type_to_extraction_method = {
        ActivityType.CRICKET_MATCH: openai_service.extract_cricket_match_data,
        ActivityType.CRICKET_COACHING: openai_service.extract_cricket_coaching_data,
        ActivityType.REST_DAY: openai_service.extract_rest_day_data,
        ActivityType.FITNESS: openai_service.extract_fitness_data,
    }
    extraction_method = activity_type_to_extraction_method[conversation.activity_type]
    extracted_data = await extraction_method(user_message.user_message)
    logger.info("extracted_data: %s", extracted_data)

    # create ai conversation message
    try:
        ai_message = ChatMessageBase(
            conversation_id=conversation.id,
            sender=ChatMessageSender.AI,
            user_message=None,
            ai_extraction=extracted_data,
            is_read=True,
            is_completed=True,
        )
        ai_message_read = await conversation_message_repository.create(ai_message)
    except ChatMessageCreationError as e:
        logger.exception("Failed to create ai message")
        raise e.to_http_exception() from None

    # get follow up questions
    ai_service = await dep_container.aget(AIService)

    follow_up_question = await ai_service.generate_follow_up_question(
        collected_data=ai_message_read.ai_extraction,
        activity_type=conversation.activity_type,
        user_message=user_message.user_message,
        model_name=settings.openai.gpt_model,
        turn_number=1,  # First turn
        use_rule_based=True,  # Use rule-based by default
    )

    if not follow_up_question:
        return ai_message_read

    try:
        if ai_message_read.ai_extraction is not None:
            ai_message_read.ai_extraction["follow_up_question"] = follow_up_question
        # convert ChatMessage to ChatMessageBase
        ai_message_base = ChatMessageBase.model_validate(ai_message_read)
        return await conversation_message_repository.update(
            ai_message_read.id,
            ai_message_base,
        )
    except ChatMessageCreationError as e:
        logger.exception("Failed to create follow up question message")
        raise e.to_http_exception() from None
