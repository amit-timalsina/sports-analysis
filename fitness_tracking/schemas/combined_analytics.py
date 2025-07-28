from common.schemas import AppBaseModel
from fitness_tracking.schemas.cricket_analytics import CricketAnalytics


class CombinedAnalytics(AppBaseModel):
    """Schema for combined fitness and cricket analytics."""

    fitness_analytics: dict[str, float]  # FitnessAnalytics data
    cricket_analytics: CricketAnalytics
    correlations: dict[str, float]  # Fitness-cricket performance correlations
    overall_recommendations: list[str]
