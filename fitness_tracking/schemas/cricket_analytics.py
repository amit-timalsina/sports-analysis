from common.schemas import AppBaseModel


class CricketAnalytics(AppBaseModel):
    """Schema for cricket analytics and insights."""

    total_coaching_sessions: int
    total_matches: int
    total_rest_days: int
    average_self_assessment: float
    batting_average: float | None
    keeping_success_rate: float | None
    most_practiced_skill: str
    confidence_trend: dict[str, float]
    improvement_areas: list[str]
    recommendations: list[str]
