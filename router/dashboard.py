from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from fitness_tracking.repositories.fitness_repository import FitnessRepository
from database.config.engine import get_database_session
from common.schemas import  SuccessResponse
from fitness_tracking.repositories.cricket_repository import (
    CricketCoachingRepository,
    CricketMatchRepository,
    RestDayRepository,
)
import logging
from fitness_tracking.repositories.fitness_repository import FitnessRepository
from datetime import UTC, datetime


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analytics",tags=["Analytics"])

@router.get("/api/dashboard")
async def get_user_dashboard(
    user_id: str = "demo_user",  # TODO: Get from authentication
    session: AsyncSession = Depends(get_database_session),
) -> SuccessResponse:
    """Get comprehensive dashboard data for a user."""
    try:
        # Get recent entries from all types
        fitness_repo = FitnessRepository(session)
        cricket_coaching_repo = CricketCoachingRepository(session)
        cricket_match_repo = CricketMatchRepository(session)
        rest_repo = RestDayRepository(session)

        # Get recent data (last 7 days)
        recent_fitness = await fitness_repo.get_recent_entries(user_id, limit=5, days_back=7)
        recent_coaching = await cricket_coaching_repo.read_multi(limit=3)
        recent_matches = await cricket_match_repo.read_multi(limit=3)
        recent_rest = await rest_repo.read_multi(limit=3)

        # Get quick analytics
        fitness_analytics = await fitness_repo.get_fitness_analytics(user_id, days_back=7)

        # Activity summary for this week
        activity_summary = {
            "fitness_sessions": len(recent_fitness),
            "cricket_coaching_sessions": len(recent_coaching),
            "matches_played": len(recent_matches),
            "rest_days": len(recent_rest),
            "average_energy_level": fitness_analytics.average_energy_level,
            "weekly_frequency": fitness_analytics.weekly_frequency,
        }

        return SuccessResponse(
            message="Dashboard data retrieved successfully",
            data={
                "user_id": user_id,
                "activity_summary": activity_summary,
                "recent_entries": {
                    "fitness": [entry.model_dump() for entry in recent_fitness],
                    "cricket_coaching": [entry.model_dump() for entry in recent_coaching],
                    "cricket_matches": [entry.model_dump() for entry in recent_matches],
                    "rest_days": [entry.model_dump() for entry in recent_rest],
                },
                "quick_insights": {
                    "most_common_fitness_activity": fitness_analytics.most_common_activity,
                    "fitness_improvement_trends": fitness_analytics.improvement_trends,
                    "recommendations": fitness_analytics.recommendations[:3],
                },
                "generated_at": datetime.now(UTC).isoformat(),
            },
        )
    except Exception as e:
        logger.exception("Failed to get dashboard data")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve dashboard data: {e}",
        ) from e