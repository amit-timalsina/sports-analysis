from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends,HTTPException,APIRouter
from database.config.engine import get_database_session
from common.schemas import  SuccessResponse
from fitness_tracking.repositories.cricket_repository import (
    CricketCoachingRepository,
    CricketMatchRepository,
    RestDayRepository,
)
import logging
from fitness_tracking.repositories.fitness_repository import FitnessRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/entries",tags=['Fitness Entries'])

@router.get("/fitness")
async def get_fitness_entries(
    limit: int = 10,
    days_back: int = 30,
    user_id: str = "demo_user",  # TODO: Get from authentication
    session: AsyncSession = Depends(get_database_session),
) -> SuccessResponse:
    """Get recent fitness entries for a user."""
    try:
        fitness_repo = FitnessRepository(session)
        entries = await fitness_repo.get_recent_entries(
            user_id=user_id,
            limit=limit,
            days_back=days_back,
        )

        return SuccessResponse(
            message="Fitness entries retrieved successfully",
            data={
                "entries": [entry.model_dump() for entry in entries],
                "total_count": len(entries),
                "user_id": user_id,
                "days_back": days_back,
            },
        )
    except Exception as e:
        logger.exception("Failed to get fitness entries")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve fitness entries: {e}",
        ) from e


@router.get("/cricket/coaching")
async def get_cricket_coaching_entries(
    limit: int = 10,
    user_id: str = "demo_user",  # TODO: Get from authentication
    session: AsyncSession = Depends(get_database_session),
) -> SuccessResponse:
    """Get cricket coaching session entries for a user."""
    try:
        cricket_repo = CricketCoachingRepository(session)
        entries = await cricket_repo.read_multi(limit=limit)

        return SuccessResponse(
            message="Cricket coaching entries retrieved successfully",
            data={
                "entries": [entry.model_dump() for entry in entries],
                "total_count": len(entries),
                "user_id": user_id,
            },
        )
    except Exception as e:
        logger.exception("Failed to get cricket coaching entries")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve cricket coaching entries: {e}",
        ) from e


@router.get("/cricket/matches")
async def get_cricket_match_entries(
    limit: int = 10,
    user_id: str = "demo_user",  # TODO: Get from authentication
    session: AsyncSession = Depends(get_database_session),
) -> SuccessResponse:
    """Get cricket match performance entries for a user."""
    try:
        match_repo = CricketMatchRepository(session)
        entries = await match_repo.read_multi(limit=limit)

        return SuccessResponse(
            message="Cricket match entries retrieved successfully",
            data={
                "entries": [entry.model_dump() for entry in entries],
                "total_count": len(entries),
                "user_id": user_id,
            },
        )
    except Exception as e:
        logger.exception("Failed to get cricket match entries")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve cricket match entries: {e}",
        ) from e


@router.get("/rest-days")
async def get_rest_day_entries(
    limit: int = 10,
    user_id: str = "demo_user",  # TODO: Get from authentication
    session: AsyncSession = Depends(get_database_session),
) -> SuccessResponse:
    """Get rest day entries for a user."""
    try:
        rest_repo = RestDayRepository(session)
        entries = await rest_repo.read_multi(limit=limit)

        return SuccessResponse(
            message="Rest day entries retrieved successfully",
            data={
                "entries": [entry.model_dump() for entry in entries],
                "total_count": len(entries),
                "user_id": user_id,
            },
        )
    except Exception as e:
        logger.exception("Failed to get rest day entries")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve rest day entries: {e}",
        ) from e
