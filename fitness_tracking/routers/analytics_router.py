"""Fitness analytics routes."""

from collections import defaultdict
from datetime import UTC, datetime, timedelta
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
from fitness_tracking.repositories.cricket_match_repository import (
    CricketMatchEntryRepository,
)
from fitness_tracking.repositories.fitness_repository import FitnessEntryRepository
from fitness_tracking.repositories.rest_day_repository import RestDayEntryRepository
from logger import get_logger

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

logger = get_logger(__name__)


@router.get("/fitness")
async def get_fitness_analytics(
    current_user: Annotated[UserGet, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    days_back: int = 30,
    user_id: str = "demo_user",
) -> SuccessResponse:
    """Get fitness analytics."""
    try:
        repository = FitnessEntryRepository(session)
        entries = await repository.read_recent_entries(
            current_user=current_user,
            days=days_back,
            limit=1000,
        )

        total_sessions = len(entries)
        if total_sessions == 0:
            return SuccessResponse(
                message="Fitness analytics retrieved successfully",
                data={
                    "total_sessions": 0,
                    "total_duration_minutes": 0,
                    "average_duration_minutes": 0,
                    "total_calories_burned": 0,
                    "average_energy_level": 0,
                    "days_analyzed": days_back,
                    "user_id": current_user.id if current_user else user_id,
                    "exercise_types_distribution": {},
                    "intensity_distribution": {},
                    "weekly_frequency": [],
                    "daily_calories": [],
                    "energy_trends": [],
                    "most_common_exercise_type": None,
                    "best_day_of_week": None,
                    "average_workout_rating": 0,
                },
            )

        # Basic calculations
        total_duration = sum(entry.duration_minutes for entry in entries)
        avg_duration = total_duration / total_sessions
        total_calories = sum(entry.calories_burned or 0 for entry in entries)

        # Energy level analysis
        energy_levels = [entry.energy_level for entry in entries if entry.energy_level]
        avg_energy = sum(energy_levels) / len(energy_levels) if energy_levels else 0

        # Workout ratings
        ratings = [entry.workout_rating for entry in entries if entry.workout_rating]
        avg_rating = sum(ratings) / len(ratings) if ratings else 0

        # Exercise type distribution
        exercise_types: defaultdict[str, int] = defaultdict(int)
        for entry in entries:
            exercise_types[entry.exercise_type] += 1
        most_common_exercise = (
            max(exercise_types.items(), key=lambda x: x[1])[0] if exercise_types else None
        )

        # Intensity distribution
        intensity_dist: defaultdict[str, int] = defaultdict(int)
        for entry in entries:
            intensity_dist[entry.intensity] += 1

        # Weekly frequency analysis (last 7 days)
        weekly_data = []
        now = datetime.now(UTC)
        for i in range(7):
            day = now - timedelta(days=i)
            day_entries = [e for e in entries if e.created_at.date() == day.date()]
            weekly_data.append(
                {
                    "date": day.strftime("%Y-%m-%d"),
                    "day_name": day.strftime("%A"),
                    "sessions_count": len(day_entries),
                    "total_duration": sum(e.duration_minutes for e in day_entries),
                    "total_calories": sum(e.calories_burned or 0 for e in day_entries),
                },
            )

        # Daily calories for the past week
        daily_calories = [{"date": d["date"], "calories": d["total_calories"]} for d in weekly_data]

        # Energy trends over time
        energy_trends = [
            {
                "date": entry.created_at.strftime("%Y-%m-%d"),
                "energy": entry.energy_level,
            }
            for entry in entries[-14:]
            if entry.energy_level
        ]

        # Best day of week analysis
        day_counts: defaultdict[str, int] = defaultdict(int)
        for entry in entries:
            day_counts[entry.created_at.strftime("%A")] += 1
        best_day = max(day_counts.items(), key=lambda x: x[1])[0] if day_counts else None

        return SuccessResponse(
            message="Fitness analytics retrieved successfully",
            data={
                "total_sessions": total_sessions,
                "total_duration_minutes": total_duration,
                "average_duration_minutes": round(avg_duration, 1),
                "total_calories_burned": total_calories,
                "average_energy_level": round(avg_energy, 1),
                "average_workout_rating": round(avg_rating, 1),
                "days_analyzed": days_back,
                "user_id": current_user.id if current_user else user_id,
                "exercise_types_distribution": dict(exercise_types),
                "intensity_distribution": dict(intensity_dist),
                "weekly_frequency": weekly_data,
                "daily_calories": daily_calories,
                "energy_trends": energy_trends,
                "most_common_exercise_type": most_common_exercise,
                "best_day_of_week": best_day,
            },
        )
    except Exception as e:
        logger.exception("Failed to get fitness analytics")
        raise HTTPException(status_code=500, detail="Failed to retrieve fitness analytics") from e


@router.get("/cricket")
async def get_cricket_analytics(
    current_user: Annotated[UserGet, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    days_back: int = 30,
    user_id: str = "demo_user",
) -> SuccessResponse:
    """Get cricket analytics."""
    try:
        match_repository = CricketMatchEntryRepository(session)
        coaching_repository = CricketCoachingEntryRepository(session)

        # Get match statistics
        match_stats = await match_repository.get_performance_stats(current_user=current_user)

        # Get coaching statistics
        coaching_stats = await coaching_repository.get_coaching_stats(current_user=current_user)

        # Combine the statistics
        combined_stats = {
            "total_matches": match_stats.get("total_matches", 0),
            "total_coaching_sessions": coaching_stats.get("total_coaching_sessions", 0),
            "total_cricket_activities": match_stats.get("total_matches", 0)
            + coaching_stats.get("total_coaching_sessions", 0),
            "average_runs": match_stats.get("average_runs", 0),
            "total_runs": match_stats.get("total_runs", 0),
            "total_wickets": match_stats.get("total_wickets", 0),
            "average_performance": match_stats.get("average_performance", 0),
            "average_self_assessment": coaching_stats.get("average_self_assessment", 0),
            "average_coach_rating": coaching_stats.get("average_coach_rating", 0),
            "average_session_duration": coaching_stats.get("average_session_duration", 0),
            "results_breakdown": match_stats.get("results_breakdown", {}),
            "focus_areas_breakdown": coaching_stats.get("focus_areas_breakdown", {}),
            "discipline_breakdown": coaching_stats.get("discipline_breakdown", {}),
            "days_analyzed": days_back,
            "user_id": current_user.id if current_user else user_id,
        }

        return SuccessResponse(
            message="Cricket analytics retrieved successfully",
            data=combined_stats,
        )
    except Exception as e:
        logger.exception("Failed to get cricket analytics")
        raise HTTPException(status_code=500, detail="Failed to retrieve cricket analytics") from e


@router.get("/combined")
async def get_combined_analytics(
    current_user: Annotated[UserGet, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    days_back: int = 30,
    user_id: str = "demo_user",
) -> SuccessResponse:
    """Get combined analytics across all activity types."""
    try:
        fitness_repository = FitnessEntryRepository(session)
        match_repository = CricketMatchEntryRepository(session)
        coaching_repository = CricketCoachingEntryRepository(session)
        rest_repository = RestDayEntryRepository(session)

        fitness_entries = await fitness_repository.read_recent_entries(
            current_user=current_user,
            days=days_back,
            limit=1000,
        )

        cricket_match_stats = await match_repository.get_performance_stats(
            current_user=current_user
        )
        cricket_coaching_stats = await coaching_repository.get_coaching_stats(
            current_user=current_user
        )
        rest_stats = await rest_repository.get_rest_stats(current_user=current_user)

        total_fitness_sessions = len(fitness_entries)
        total_cricket_matches = cricket_match_stats.get("total_matches", 0)
        total_cricket_coaching = cricket_coaching_stats.get("total_coaching_sessions", 0)
        total_cricket_activities = total_cricket_matches + total_cricket_coaching
        total_rest_days = rest_stats.get("total_rest_days", 0)
        total_activities = total_fitness_sessions + total_cricket_activities + total_rest_days

        if total_fitness_sessions > 0:
            total_fitness_duration = sum(entry.duration_minutes for entry in fitness_entries)
        else:
            total_fitness_duration = 0

        return SuccessResponse(
            message="Combined analytics retrieved successfully",
            data={
                "total_activities": total_activities,
                "fitness_analytics": {
                    "total_sessions": total_fitness_sessions,
                    "total_duration_minutes": total_fitness_duration,
                },
                "cricket_analytics": {
                    "total_matches": total_cricket_matches,
                    "total_coaching_sessions": total_cricket_coaching,
                    "total_cricket_activities": total_cricket_activities,
                    "match_stats": cricket_match_stats,
                    "coaching_stats": cricket_coaching_stats,
                },
                "rest_analytics": {
                    "total_rest_days": total_rest_days,
                    "average_sleep_hours": rest_stats.get("average_sleep_hours", 0),
                    "average_sleep_quality": rest_stats.get("average_sleep_quality", 0),
                    "average_recovery_score": rest_stats.get("average_recovery_score", 0),
                    "average_readiness": rest_stats.get("average_readiness", 0),
                    "rest_type_breakdown": rest_stats.get("rest_type_breakdown", {}),
                    "planned_breakdown": rest_stats.get("planned_breakdown", {}),
                },
                "activity_breakdown": {
                    "fitness_percentage": round(
                        (total_fitness_sessions / total_activities * 100),
                        1,
                    )
                    if total_activities > 0
                    else 0,
                    "cricket_matches_percentage": round(
                        (total_cricket_matches / total_activities * 100), 1
                    )
                    if total_activities > 0
                    else 0,
                    "cricket_coaching_percentage": round(
                        (total_cricket_coaching / total_activities * 100), 1
                    )
                    if total_activities > 0
                    else 0,
                    "rest_days_percentage": round((total_rest_days / total_activities * 100), 1)
                    if total_activities > 0
                    else 0,
                },
                "days_analyzed": days_back,
                "user_id": current_user.id if current_user else user_id,
            },
        )
    except Exception as e:
        logger.exception("Failed to get combined analytics")
        raise HTTPException(status_code=500, detail="Failed to retrieve combined analytics") from e
