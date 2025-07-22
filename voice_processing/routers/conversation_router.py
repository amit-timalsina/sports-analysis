"""Audio management routes."""

import logging
from typing import Annotated

import svcs
from fastapi import APIRouter, Depends

from auth.dependencies.security import get_current_user
from auth.schemas.user import User
from voice_processing.exceptions.conversation_errors import ConversationCreationError
from voice_processing.repositories.conversation_repository import ConversationRepository
from voice_processing.schemas.conversation import ConversationCreate, ConversationRead

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/conversations", tags=["conversations"])


@router.post("", response_model=ConversationRead)
async def create_conversation(
    conversation: ConversationCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    dep_container: svcs.fastapi.DepContainer,
) -> ConversationRead:
    """Create a new conversation."""
    conversation_repository = await dep_container.aget(ConversationRepository)
    try:
        return await conversation_repository.create(conversation, current_user)
    except ConversationCreationError as e:
        logger.exception("Failed to create conversation")
        raise e.to_http_exception() from None
