from collections.abc import AsyncGenerator

import svcs
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

from auth.repositories.user_repository import UserRepository
from auth.services.supabase import AuthSupabaseService
from database.session import get_session
from fitness_tracking.repositories.cricket_coaching_repository import CricketCoachingEntryRepository
from fitness_tracking.repositories.fitness_repository import FitnessEntryRepository
from logger import get_logger
from voice_processing.repositories.chat_message_repository import ChatMessageRepository
from voice_processing.repositories.conversation_repository import (
    ConversationRepository,
)
from voice_processing.services.ai_service import AIService
from voice_processing.services.openai_service import OpenAIService

logger = get_logger(__name__)


async def lifespan(_: FastAPI, registry: svcs.Registry) -> AsyncGenerator[None, None]:
    """
    Lifespan event handler.

    This method is called when the application starts and shuts down.
    It's used to setup and teardown resources that should exist for the lifespan
    of the application.

    Args:
    ----
        app: The FastAPI application instance.
        registry: The dependency injection registry.

    """
    # Register Dependecies
    registry.register_factory(AsyncSession, get_session)
    registry.register_factory(AuthSupabaseService, AuthSupabaseService.get_as_dependency)
    registry.register_factory(UserRepository, UserRepository.get_as_dependency)
    registry.register_factory(ConversationRepository, ConversationRepository.get_as_dependency)
    registry.register_factory(
        ChatMessageRepository,
        ChatMessageRepository.get_as_dependency,
    )
    registry.register_factory(OpenAIService, OpenAIService.get_as_dependency)
    registry.register_factory(AIService, AIService.get_as_dependency)
    registry.register_factory(
        CricketCoachingEntryRepository,
        CricketCoachingEntryRepository.get_as_dependency,
    )
    registry.register_factory(
        FitnessEntryRepository,
        FitnessEntryRepository.get_as_dependency,
    )
    yield
    # Teardown Resources
    logger.info("Shutting down application.")
    await registry.aclose()
