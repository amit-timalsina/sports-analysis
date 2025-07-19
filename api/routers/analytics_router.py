"""Analytics and statistics routes."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from common.schemas import SuccessResponse
from database.session import get_session
from fitness_tracking.repositories import (
    CricketMatchEntryRepository,
    FitnessEntryRepository,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/fitness")
async def get_fitness_analytics(
    session: Annotated[AsyncSession, Depends(get_session)],
    days_back: int = 30,
    user_id: str = "demo_user",  # TODO: Get from authentication
) -> SuccessResponse:
    """Get fitness analytics using clean architecture repository."""
    try:
        repository = FitnessEntryRepository(session)
        entries = await repository.read_recent_entries(
            current_user=None,  # TODO: Pass actual user
            days=days_back,
            limit=1000,  # Get more data for analytics
        )

        # Basic analytics calculation
        total_sessions = len(entries)
        if total_sessions > 0:
            total_duration = sum(entry.duration_minutes for entry in entries)
            avg_duration = total_duration / total_sessions
            total_calories = sum(entry.calories_burned or 0 for entry in entries)
        else:
            total_duration = avg_duration = total_calories = 0

        return SuccessResponse(
            message="Fitness analytics retrieved successfully",
            data={
                "total_sessions": total_sessions,
                "total_duration_minutes": total_duration,
                "average_duration_minutes": round(avg_duration, 1),
                "total_calories_burned": total_calories,
                "days_analyzed": days_back,
                "user_id": user_id,
            },
        )
    except Exception as e:
        logger.exception("Failed to get fitness analytics")
        raise HTTPException(status_code=500, detail="Failed to retrieve fitness analytics") from e


@router.get("/cricket")
async def get_cricket_analytics(
    session: Annotated[AsyncSession, Depends(get_session)],
    days_back: int = 30,
    user_id: str = "demo_user",  # TODO: Get from authentication
) -> SuccessResponse:
    """Get cricket analytics using clean architecture repository."""
    try:
        match_repository = CricketMatchEntryRepository(session)

        # Get performance statistics
        stats = await match_repository.get_performance_stats(
            current_user=None,  # TODO: Pass actual user
        )

        return SuccessResponse(
            message="Cricket analytics retrieved successfully",
            data={
                **stats,
                "days_analyzed": days_back,
                "user_id": user_id,
            },
        )
    except Exception as e:
        logger.exception("Failed to get cricket analytics")
        raise HTTPException(status_code=500, detail="Failed to retrieve cricket analytics") from e


@router.get("/combined")
async def get_combined_analytics(
    session: Annotated[AsyncSession, Depends(get_session)],
    days_back: int = 30,
    user_id: str = "demo_user",  # TODO: Get from authentication
) -> SuccessResponse:
    """Get combined analytics across all activity types using clean architecture repositories."""
    try:
        fitness_repository = FitnessEntryRepository(session)
        match_repository = CricketMatchEntryRepository(session)

        # Get fitness data
        fitness_entries = await fitness_repository.read_recent_entries(
            current_user=None,  # TODO: Pass actual user
            days=days_back,
            limit=1000,
        )

        # Get cricket stats
        cricket_stats = await match_repository.get_performance_stats(
            current_user=None,  # TODO: Pass actual user
        )

        # Combined analytics
        total_fitness_sessions = len(fitness_entries)
        total_cricket_matches = cricket_stats.get("total_matches", 0)
        total_activities = total_fitness_sessions + total_cricket_matches

        if total_fitness_sessions > 0:
            total_fitness_duration = sum(entry.duration_minutes for entry in fitness_entries)
        else:
            total_fitness_duration = 0

        return SuccessResponse(
            message="Combined analytics retrieved successfully",
            data={
                "total_activities": total_activities,
                "fitness": {
                    "total_sessions": total_fitness_sessions,
                    "total_duration_minutes": total_fitness_duration,
                },
                "cricket": cricket_stats,
                "activity_breakdown": {
                    "fitness_percentage": round(
                        (total_fitness_sessions / total_activities * 100),
                        1,
                    )
                    if total_activities > 0
                    else 0,
                    "cricket_percentage": round((total_cricket_matches / total_activities * 100), 1)
                    if total_activities > 0
                    else 0,
                },
                "days_analyzed": days_back,
                "user_id": user_id,
            },
        )
    except Exception as e:
        logger.exception("Failed to get combined analytics")
        raise HTTPException(status_code=500, detail="Failed to retrieve combined analytics") from e
