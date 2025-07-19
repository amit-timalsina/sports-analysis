"""Data entry retrieval endpoints for the application."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from common.schemas import SuccessResponse
from database.session import get_session
from fitness_tracking.repositories import (
    CricketCoachingEntryRepository,
    CricketMatchEntryRepository,
    FitnessEntryRepository,
    RestDayEntryRepository,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/entries", tags=["entries"])


# API endpoints for data retrieval - using new clean architecture repositories
@router.get("/fitness")
async def get_fitness_entries(
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: int = 10,
    days_back: int = 30,
    user_id: str = "demo_user",  # TODO: Get from authentication
) -> SuccessResponse:
    """Get recent fitness entries using clean architecture repository."""
    try:
        repository = FitnessEntryRepository(session)
        entries = await repository.read_recent_entries(
            current_user=None,  # TODO: Pass actual user
            days=days_back,
            limit=limit,
        )

        return SuccessResponse(
            message="Fitness entries retrieved successfully",
            data={
                "entries": [entry.model_dump(mode="json") for entry in entries],
                "count": len(entries),
                "user_id": user_id,
                "days_back": days_back,
            },
        )
    except Exception as e:
        logger.exception("Failed to get fitness entries")
        raise HTTPException(status_code=500, detail="Failed to retrieve fitness entries") from e


@router.get("/cricket/coaching")
async def get_cricket_coaching_entries(
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: int = 10,
    user_id: str = "demo_user",  # TODO: Get from authentication
) -> SuccessResponse:
    """Get recent cricket coaching entries using clean architecture repository."""
    try:
        repository = CricketCoachingEntryRepository(session)
        entries = await repository.read_multi(
            current_user=None,  # TODO: Pass actual user
            limit=limit,
        )

        return SuccessResponse(
            message="Cricket coaching entries retrieved successfully",
            data={
                "entries": [entry.model_dump(mode="json") for entry in entries],
                "count": len(entries),
                "user_id": user_id,
            },
        )
    except Exception as e:
        logger.exception("Failed to get cricket coaching entries")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve cricket coaching entries",
        ) from e


@router.get("/cricket/matches")
async def get_cricket_match_entries(
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: int = 10,
    user_id: str = "demo_user",  # TODO: Get from authentication
) -> SuccessResponse:
    """Get recent cricket match entries using clean architecture repository."""
    try:
        repository = CricketMatchEntryRepository(session)
        entries = await repository.read_multi(
            current_user=None,  # TODO: Pass actual user
            limit=limit,
        )

        return SuccessResponse(
            message="Cricket match entries retrieved successfully",
            data={
                "entries": [entry.model_dump(mode="json") for entry in entries],
                "count": len(entries),
                "user_id": user_id,
            },
        )
    except Exception as e:
        logger.exception("Failed to get cricket match entries")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve cricket match entries",
        ) from e


@router.get("/rest-days")
async def get_rest_day_entries(
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: int = 10,
    user_id: str = "demo_user",  # TODO: Get from authentication
) -> SuccessResponse:
    """Get recent rest day entries using clean architecture repository."""
    try:
        repository = RestDayEntryRepository(session)
        entries = await repository.read_multi(
            current_user=None,  # TODO: Pass actual user
            limit=limit,
        )

        return SuccessResponse(
            message="Rest day entries retrieved successfully",
            data={
                "entries": [entry.model_dump(mode="json") for entry in entries],
                "count": len(entries),
                "user_id": user_id,
            },
        )
    except Exception as e:
        logger.exception("Failed to get rest day entries")
        raise HTTPException(status_code=500, detail="Failed to retrieve rest day entries") from e
