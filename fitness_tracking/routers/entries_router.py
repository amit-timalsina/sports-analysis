"""Fitness entries routes."""

import logging
from typing import Annotated

import svcs
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from auth.dependencies.security import get_current_user
from auth.schemas.user import User as UserGet
from database.session import get_session
from fitness_tracking.exceptions.fitness_errors import (
    CricketCoachingEntryCreationError,
    CricketMatchEntryCreationError,
    FitnessEntryCreationError,
    RestDayEntryCreationError,
)
from fitness_tracking.repositories.cricket_coaching_repository import CricketCoachingEntryRepository
from fitness_tracking.repositories.cricket_match_repository import (
    CricketMatchEntryRepository,
)
from fitness_tracking.repositories.fitness_repository import FitnessEntryRepository
from fitness_tracking.repositories.rest_day_repository import RestDayEntryRepository
from fitness_tracking.schemas.cricket_coaching import (
    CricketCoachingEntryCreate,
    CricketCoachingEntryRead,
    CricketCoachingEntryResponse,
)
from fitness_tracking.schemas.cricket_match import (
    CricketMatchEntryCreate,
    CricketMatchEntryRead,
    CricketMatchEntryResponse,
)
from fitness_tracking.schemas.fitness import (
    FitnessEntryCreate,
    FitnessEntryRead,
    FitnessEntryResponse,
)
from fitness_tracking.schemas.rest_day import (
    RestDayEntryCreate,
    RestDayEntryRead,
    RestDayEntryResponse,
)
from voice_processing.repositories.chat_message_repository import ChatMessageRepository
from voice_processing.schemas.chat_message_sender import ChatMessageSender

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/entries", tags=["entries"])


@router.post("/fitness")
async def create_fitness_entry(
    entry: FitnessEntryCreate,
    current_user: Annotated[UserGet, Depends(get_current_user)],
    dep_container: svcs.fastapi.DepContainer,
) -> FitnessEntryRead:
    """Create a new fitness entry."""
    repository = await dep_container.aget(FitnessEntryRepository)
    try:
        return await repository.create(entry, current_user)
    except FitnessEntryCreationError as e:
        logger.exception("Failed to create fitness entry")
        raise e.to_http_exception() from None


@router.get("/fitness", response_model=FitnessEntryResponse)
async def get_fitness_entries(
    current_user: Annotated[UserGet, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: int = 10,
    days_back: int = 30,
) -> FitnessEntryResponse:
    """Get recent fitness entries with transcription data."""
    try:
        repository = FitnessEntryRepository(session)
        entries = await repository.read_recent_entries(
            current_user=current_user,
            days=days_back,
            limit=limit,
        )

        # Get transcription data from conversations
        transcriptions: list[list[str]] = []
        chat_message_repository = ChatMessageRepository(session)

        for entry in entries:
            if entry.conversation_id:
                user_messages = await chat_message_repository.read_multi_by_filter(
                    filter_condition=(
                        (chat_message_repository.model.conversation_id == entry.conversation_id)
                        & (chat_message_repository.model.sender == ChatMessageSender.USER)
                        & (chat_message_repository.model.user_message.is_not(None))
                    ),
                    current_user=current_user,
                    limit=100,
                )
                if user_messages:
                    entry_transcriptions = [
                        msg.user_message for msg in user_messages if msg.user_message
                    ]
                    transcriptions.append(entry_transcriptions)
                else:
                    transcriptions.append([])
            else:
                transcriptions.append([])
        return FitnessEntryResponse(
            entries=entries,
            count=len(entries),
            user_id=current_user.id,
            days_back=days_back,
            transcriptions=transcriptions,
        )
    except Exception as e:
        logger.exception("Failed to get fitness entries")
        raise HTTPException(status_code=500, detail="Failed to retrieve fitness entries") from e


@router.post("/cricket/coaching")
async def create_cricket_coaching_entry(
    entry: CricketCoachingEntryCreate,
    current_user: Annotated[UserGet, Depends(get_current_user)],
    dep_container: svcs.fastapi.DepContainer,
) -> CricketCoachingEntryRead:
    """Create a new cricket coaching entry."""
    repository = await dep_container.aget(CricketCoachingEntryRepository)
    try:
        return await repository.create(entry, current_user)
    except CricketCoachingEntryCreationError as e:
        logger.exception("Failed to create cricket coaching entry")
        raise e.to_http_exception() from None


@router.get("/cricket/coaching", response_model=CricketCoachingEntryResponse)
async def get_cricket_coaching_entries(
    current_user: Annotated[UserGet, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: int = 10,
) -> CricketCoachingEntryResponse:
    """Get recent cricket coaching entries with transcription data."""
    try:
        repository = CricketCoachingEntryRepository(session)
        entries = await repository.read_multi(
            current_user=current_user,
            limit=limit,
        )

        # Get transcription data from conversations
        transcriptions = []
        chat_message_repository = ChatMessageRepository(session)

        for entry in entries:
            if entry.conversation_id:
                user_messages = await chat_message_repository.read_multi_by_filter(
                    filter_condition=(
                        (chat_message_repository.model.conversation_id == entry.conversation_id)
                        & (chat_message_repository.model.sender == ChatMessageSender.USER)
                        & (chat_message_repository.model.user_message.is_not(None))
                    ),
                    current_user=current_user,
                    limit=100,
                )
                if user_messages:
                    entry_transcriptions = [
                        msg.user_message for msg in user_messages if msg.user_message
                    ]
                    transcriptions.append(entry_transcriptions)
                else:
                    transcriptions.append([])
            else:
                transcriptions.append([])
        return CricketCoachingEntryResponse(
            entries=entries,
            count=len(entries),
            user_id=current_user.id,
            transcriptions=transcriptions,
        )
    except Exception as e:
        logger.exception("Failed to get cricket coaching entries")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve cricket coaching entries",
        ) from e


@router.post("/cricket/matches")
async def create_cricket_match_entry(
    entry: CricketMatchEntryCreate,
    current_user: Annotated[UserGet, Depends(get_current_user)],
    dep_container: svcs.fastapi.DepContainer,
) -> CricketMatchEntryRead:
    """Create a new cricket match entry."""
    repository = await dep_container.aget(CricketMatchEntryRepository)
    try:
        return await repository.create(entry, current_user)
    except CricketMatchEntryCreationError as e:
        logger.exception("Failed to create cricket match entry")
        raise e.to_http_exception() from None


@router.get("/cricket/matches", response_model=CricketMatchEntryResponse)
async def get_cricket_match_entries(
    current_user: Annotated[UserGet, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: int = 10,
) -> CricketMatchEntryResponse:
    """Get recent cricket match entries with transcription data."""
    try:
        repository = CricketMatchEntryRepository(session)
        entries = await repository.read_multi(
            current_user=current_user,
            limit=limit,
        )

        # Get transcription data from conversations
        transcriptions = []
        chat_message_repository = ChatMessageRepository(session)

        for entry in entries:
            if entry.conversation_id:
                user_messages = await chat_message_repository.read_multi_by_filter(
                    filter_condition=(
                        (chat_message_repository.model.conversation_id == entry.conversation_id)
                        & (chat_message_repository.model.sender == ChatMessageSender.USER)
                        & (chat_message_repository.model.user_message.is_not(None))
                    ),
                    current_user=current_user,
                    limit=100,
                )
                if user_messages:
                    entry_transcriptions = [
                        msg.user_message for msg in user_messages if msg.user_message
                    ]
                    transcriptions.append(entry_transcriptions)
                else:
                    transcriptions.append([])
            else:
                transcriptions.append([])
        return CricketMatchEntryResponse(
            entries=entries,
            count=len(entries),
            user_id=current_user.id,
            transcriptions=transcriptions,
        )
    except Exception as e:
        logger.exception("Failed to get cricket match entries")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve cricket match entries",
        ) from e


@router.post("/rest-days")
async def create_rest_day_entry(
    entry: RestDayEntryCreate,
    current_user: Annotated[UserGet, Depends(get_current_user)],
    dep_container: svcs.fastapi.DepContainer,
) -> RestDayEntryRead:
    """Create a new rest day entry."""
    repository = await dep_container.aget(RestDayEntryRepository)
    try:
        return await repository.create(entry, current_user)
    except RestDayEntryCreationError as e:
        logger.exception("Failed to create rest day entry")
        raise e.to_http_exception() from None


@router.get("/rest-days", response_model=RestDayEntryResponse)
async def get_rest_day_entries(
    current_user: Annotated[UserGet, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: int = 10,
) -> RestDayEntryResponse:
    """Get recent rest day entries with transcription data."""
    try:
        repository = RestDayEntryRepository(session)
        entries = await repository.read_multi(
            current_user=current_user,
            limit=limit,
        )

        # Get transcription data from conversations
        transcriptions = []
        chat_message_repository = ChatMessageRepository(session)

        for entry in entries:
            if entry.conversation_id:
                user_messages = await chat_message_repository.read_multi_by_filter(
                    filter_condition=(
                        (chat_message_repository.model.conversation_id == entry.conversation_id)
                        & (chat_message_repository.model.sender == ChatMessageSender.USER)
                        & (chat_message_repository.model.user_message.is_not(None))
                    ),
                    current_user=current_user,
                    limit=100,
                )
                if user_messages:
                    entry_transcriptions = [
                        msg.user_message for msg in user_messages if msg.user_message
                    ]
                    transcriptions.append(entry_transcriptions)
                else:
                    transcriptions.append([])
            else:
                transcriptions.append([])
        return RestDayEntryResponse(
            entries=entries,
            count=len(entries),
            user_id=current_user.id,
            transcriptions=transcriptions,
        )
    except Exception as e:
        logger.exception("Failed to get rest day entries")
        raise HTTPException(status_code=500, detail="Failed to retrieve rest day entries") from e
