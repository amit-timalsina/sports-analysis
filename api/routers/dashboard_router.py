"""Dashboard data routes."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from common.schemas import SuccessResponse
from database.session import get_session
from fitness_tracking.repositories import (
    CricketCoachingEntryRepository,
    FitnessEntryRepository,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["dashboard"])


@router.get("/dashboard")
async def get_user_dashboard(
    session: Annotated[AsyncSession, Depends(get_session)],
    user_id: str = "demo_user",  # TODO: Get from authentication
) -> SuccessResponse:
    """Get comprehensive user dashboard data using clean architecture repositories."""
    try:
        fitness_repository = FitnessEntryRepository(session)
        coaching_repository = CricketCoachingEntryRepository(session)

        # Get recent entries (last 7 days for dashboard)
        recent_fitness = await fitness_repository.read_recent_entries(
            current_user=None,  # TODO: Pass actual user
            days=7,
            limit=20,
        )

        recent_coaching = await coaching_repository.read_multi(
            current_user=None,  # TODO: Pass actual user
            limit=10,
        )

        # Quick stats
        this_week_fitness = len(recent_fitness)
        this_week_coaching = len(recent_coaching)

        return SuccessResponse(
            message="Dashboard data retrieved successfully",
            data={
                "user_id": user_id,
                "this_week": {
                    "fitness_sessions": this_week_fitness,
                    "coaching_sessions": this_week_coaching,
                    "total_activities": this_week_fitness + this_week_coaching,
                },
                "recent_activities": {
                    "fitness": [entry.model_dump(mode="json") for entry in recent_fitness[:5]],
                    "coaching": [entry.model_dump(mode="json") for entry in recent_coaching[:5]],
                },
            },
        )
    except Exception as e:
        logger.exception("Failed to get dashboard data")
        raise HTTPException(status_code=500, detail="Failed to retrieve dashboard data") from e
