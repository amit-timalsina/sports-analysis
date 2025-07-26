"""Dashboard data routes."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from auth.dependencies.security import get_current_user
from auth.schemas.user import User as UserGet
from common.schemas import SuccessResponse
from database.session import get_session
from fitness_tracking.repositories.cricket_coaching_repository import (
    CricketCoachingEntryRepository,
)
from fitness_tracking.repositories.cricket_match_repository import CricketMatchEntryRepository
from fitness_tracking.repositories.fitness_repository import FitnessEntryRepository
from fitness_tracking.repositories.rest_day_repository import RestDayEntryRepository

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["dashboard"])


@router.get("/dashboard")
async def get_user_dashboard(
    current_user: Annotated[UserGet, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    user_id: str = "demo_user",  # TODO: Get from authentication
) -> SuccessResponse:
    """Get comprehensive user dashboard data using clean architecture repositories."""
    try:
        fitness_repository = FitnessEntryRepository(session)
        coaching_repository = CricketCoachingEntryRepository(session)
        cricket_match_repository = CricketMatchEntryRepository(session)
        rest_day_repository = RestDayEntryRepository(session)
        # Get recent entries (last 7 days for dashboard)
        recent_fitness = await fitness_repository.read_recent_entries(
            current_user=current_user,  # TODO: Pass actual user
            days=7,
            limit=20,
        )

        recent_coaching = await coaching_repository.read_multi(
            current_user=current_user,
            limit=10,
        )

        recent_cricket_match = await cricket_match_repository.read_multi(
            current_user=current_user,
            limit=10,
        )

        recent_rest_day = await rest_day_repository.read_multi(
            current_user=current_user,
            limit=10,
        )

        # Quick stats
        this_week_fitness = len(recent_fitness)
        this_week_coaching = len(recent_coaching)
        this_week_cricket_match = len(recent_cricket_match)
        this_week_rest_day = len(recent_rest_day)
        this_week_total = (
            this_week_fitness + this_week_coaching + this_week_cricket_match + this_week_rest_day
        )
        return SuccessResponse(
            message="Dashboard data retrieved successfully",
            data={
                "user_id": current_user.id if current_user else user_id,
                "this_week": {
                    "fitness_sessions": this_week_fitness,
                    "coaching_sessions": this_week_coaching,
                    "cricket_match_sessions": this_week_cricket_match,
                    "rest_day_sessions": this_week_rest_day,
                    "total_activities": this_week_total,
                },
                "recent_entries": {
                    "fitness": [entry.model_dump(mode="json") for entry in recent_fitness],
                    "cricket_match": [
                        entry.model_dump(mode="json") for entry in recent_cricket_match
                    ],
                    "rest_day": [entry.model_dump(mode="json") for entry in recent_rest_day],
                    "cricket_coaching": [
                        entry.model_dump(mode="json") for entry in recent_coaching
                    ],
                },
            },
        )
    except Exception as e:
        logger.exception("Failed to get dashboard data")
        raise HTTPException(status_code=500, detail="Failed to retrieve dashboard data") from e
