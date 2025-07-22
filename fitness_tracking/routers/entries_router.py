"""Fitness entries routes."""

import logging
from typing import Annotated

import svcs
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from auth.dependencies.security import get_current_user
from auth.schemas.user import User as UserGet
from common.schemas import SuccessResponse
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
)
from fitness_tracking.schemas.cricket_match import CricketMatchEntryCreate, CricketMatchEntryRead
from fitness_tracking.schemas.fitness import FitnessEntryCreate, FitnessEntryRead
from fitness_tracking.schemas.rest_day import RestDayEntryCreate, RestDayEntryRead

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


@router.get("/fitness")
async def get_fitness_entries(
    current_user: Annotated[UserGet, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: int = 10,
    days_back: int = 30,
    user_id: str = "demo_user",
) -> SuccessResponse:
    """Get recent fitness entries."""
    try:
        repository = FitnessEntryRepository(session)
        entries = await repository.read_recent_entries(
            current_user=None,
            days=days_back,
            limit=limit,
        )

        return SuccessResponse(
            message="Fitness entries retrieved successfully",
            data={
                "entries": [entry.model_dump(mode="json") for entry in entries],
                "count": len(entries),
                "user_id": current_user.id if current_user else user_id,
                "days_back": days_back,
            },
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


@router.get("/cricket/coaching")
async def get_cricket_coaching_entries(
    current_user: Annotated[UserGet, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: int = 10,
    user_id: str = "demo_user",
) -> SuccessResponse:
    """Get recent cricket coaching entries."""
    try:
        repository = CricketCoachingEntryRepository(session)
        entries = await repository.read_multi(
            current_user=current_user,
            limit=limit,
        )

        return SuccessResponse(
            message="Cricket coaching entries retrieved successfully",
            data={
                "entries": [entry.model_dump(mode="json") for entry in entries],
                "count": len(entries),
                "user_id": current_user.id if current_user else user_id,
            },
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


@router.get("/cricket/matches")
async def get_cricket_match_entries(
    current_user: Annotated[UserGet, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: int = 10,
    user_id: str = "demo_user",
) -> SuccessResponse:
    """Get recent cricket match entries."""
    try:
        repository = CricketMatchEntryRepository(session)
        entries = await repository.read_multi(
            current_user=current_user,
            limit=limit,
        )

        return SuccessResponse(
            message="Cricket match entries retrieved successfully",
            data={
                "entries": [entry.model_dump(mode="json") for entry in entries],
                "count": len(entries),
                "user_id": current_user.id if current_user else user_id,
            },
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


@router.get("/rest-days")
async def get_rest_day_entries(
    current_user: Annotated[UserGet, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: int = 10,
    user_id: str = "demo_user",
) -> SuccessResponse:
    """Get recent rest day entries."""
    try:
        repository = RestDayEntryRepository(session)
        entries = await repository.read_multi(
            current_user=current_user,
            limit=limit,
        )

        return SuccessResponse(
            message="Rest day entries retrieved successfully",
            data={
                "entries": [entry.model_dump(mode="json") for entry in entries],
                "count": len(entries),
                "user_id": current_user.id if current_user else user_id,
            },
        )
    except Exception as e:
        logger.exception("Failed to get rest day entries")
        raise HTTPException(status_code=500, detail="Failed to retrieve rest day entries") from e
