from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from fitness_tracking.repositories.fitness_repository import FitnessRepository
from database.config.engine import get_database_session
from common.schemas import  SuccessResponse
from fitness_tracking.repositories.cricket_repository import CricketAnalyticsRepository
from fitness_tracking.repositories.fitness_repository import FitnessRepository
from datetime import UTC, datetime
import logging

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/api/analytics",tags=["Analytics"])

@router.get("/fitness")
async def get_fitness_analytics(
    days_back: int = 30,
    user_id: str = "demo_user",  # TODO: Get from authentication
    session: AsyncSession = Depends(get_database_session),
) -> SuccessResponse:
    """Get comprehensive fitness analytics for a user."""
    try:
        fitness_repo = FitnessRepository(session)
        analytics = await fitness_repo.get_fitness_analytics(
            user_id=user_id,
            days_back=days_back,
        )

        return SuccessResponse(
            message="Fitness analytics generated successfully",
            data={
                "analytics": analytics.model_dump(),
                "user_id": user_id,
                "period_days": days_back,
                "generated_at": datetime.now(UTC).isoformat(),
            },
        )
    except Exception as e:
        logger.exception("Failed to generate fitness analytics")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate fitness analytics: {e}",
        ) from e


@router.get("/cricket")
async def get_cricket_analytics(
    days_back: int = 30,
    user_id: str = "demo_user",  # TODO: Get from authentication
    session: AsyncSession = Depends(get_database_session),
) -> SuccessResponse:
    """Get comprehensive cricket analytics for a user."""
    try:
        cricket_analytics_repo = CricketAnalyticsRepository(session)
        analytics = await cricket_analytics_repo.get_cricket_analytics(
            user_id=user_id,
            days_back=days_back,
        )

        return SuccessResponse(
            message="Cricket analytics generated successfully",
            data={
                "analytics": analytics.model_dump(),
                "user_id": user_id,
                "period_days": days_back,
                "generated_at": datetime.now(UTC).isoformat(),
            },
        )
    except Exception as e:
        logger.exception("Failed to generate cricket analytics")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate cricket analytics: {e}",
        ) from e


@router.get("/combined")
async def get_combined_analytics(
    days_back: int = 30,
    user_id: str = "demo_user",  # TODO: Get from authentication
    session: AsyncSession = Depends(get_database_session),
) -> SuccessResponse:
    """Get combined fitness and cricket analytics with correlations."""
    try:
        # Get both analytics
        fitness_repo = FitnessRepository(session)
        cricket_analytics_repo = CricketAnalyticsRepository(session)

        fitness_analytics = await fitness_repo.get_fitness_analytics(user_id, days_back)
        cricket_analytics = await cricket_analytics_repo.get_cricket_analytics(user_id, days_back)

        # Simple correlation analysis (could be enhanced)
        correlations = {}
        if fitness_analytics.weekly_frequency > 0 and cricket_analytics.average_self_assessment > 0:
            correlations["fitness_frequency_vs_cricket_confidence"] = min(
                fitness_analytics.weekly_frequency
                / 7
                * cricket_analytics.average_self_assessment
                / 10,
                1.0,
            )

        # Generate combined recommendations
        combined_recommendations = []
        combined_recommendations.extend(fitness_analytics.recommendations[:2])
        combined_recommendations.extend(cricket_analytics.recommendations[:2])

        if fitness_analytics.weekly_frequency < 3:
            combined_recommendations.append(
                "Increase fitness frequency to improve cricket performance correlation",
            )

        return SuccessResponse(
            message="Combined analytics generated successfully",
            data={
                "fitness_analytics": fitness_analytics.model_dump(),
                "cricket_analytics": cricket_analytics.model_dump(),
                "correlations": correlations,
                "combined_recommendations": combined_recommendations,
                "user_id": user_id,
                "period_days": days_back,
                "generated_at": datetime.now(UTC).isoformat(),
            },
        )
    except Exception as e:
        logger.exception("Failed to generate combined analytics")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate combined analytics: {e}",
        ) from e

