import logging
from collections.abc import AsyncGenerator

import svcs
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

from auth.repositories.user_repository import UserRepository
from auth.services.supabase import AuthSupabaseService
from database.session import get_session
from voice_processing.repositories.conversation_repository import (
    ConversationAnalyticsRepository,
    ConversationMessageRepository,
    ConversationRepository,
    ConversationTurnRepository,
    QuestionContextRepository,
)

logger = logging.getLogger(__name__)


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
        ConversationMessageRepository,
        ConversationMessageRepository.get_as_dependency,
    )
    registry.register_factory(
        ConversationTurnRepository,
        ConversationTurnRepository.get_as_dependency,
    )
    registry.register_factory(
        ConversationAnalyticsRepository,
        ConversationAnalyticsRepository.get_as_dependency,
    )
    registry.register_factory(
        QuestionContextRepository,
        QuestionContextRepository.get_as_dependency,
    )
    yield
    # Teardown Resources
    logger.info("Shutting down application.")
    await registry.aclose()
