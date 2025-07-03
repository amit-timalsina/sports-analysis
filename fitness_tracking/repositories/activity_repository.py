"""Activity repositories for fitness tracking data access layer."""

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from common.repositories.crud_repository import CRUDRepository
from fitness_tracking.exceptions import (
    CricketCoachingEntryCreationError,
    CricketCoachingEntryNotFoundError,
    CricketMatchEntryCreationError,
    CricketMatchEntryNotFoundError,
    FitnessEntryCreationError,
    FitnessEntryNotFoundError,
    RestDayEntryCreationError,
    RestDayEntryNotFoundError,
)
from fitness_tracking.models import (
    CricketCoachingEntry,
    CricketMatchEntry,
    FitnessEntry,
    RestDayEntry,
)
from fitness_tracking.schemas import (
    CricketCoachingEntryCreate,
    CricketCoachingEntryRead,
    CricketCoachingEntryUpdate,
    CricketMatchEntryCreate,
    CricketMatchEntryRead,
    CricketMatchEntryUpdate,
    FitnessEntryCreate,
    FitnessEntryRead,
    FitnessEntryUpdate,
    RestDayEntryCreate,
    RestDayEntryRead,
    RestDayEntryUpdate,
)


class FitnessEntryRepository(
    CRUDRepository[
        FitnessEntry,
        FitnessEntryCreate,
        FitnessEntryRead,
        FitnessEntryUpdate,
    ],
):
    """Repository for managing fitness entry operations."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the fitness entry repository."""
        super().__init__(
            model=FitnessEntry,
            create_schema=FitnessEntryCreate,
            read_schema=FitnessEntryRead,
            update_schema=FitnessEntryUpdate,
            session=session,
            not_found_exception=FitnessEntryNotFoundError,
            creation_exception=FitnessEntryCreationError,
            user_filter=self._user_filter,
        )

    def _user_filter(self, user: Any) -> Any:
        """Filter entries by user."""
        if user:
            return FitnessEntry.user_id == user.id
        return False

    async def read_by_session_id(
        self,
        session_id: str,
        current_user: Any | None = None,
    ) -> list[FitnessEntryRead]:
        """Get fitness entries by session ID."""
        return await self.read_multi_by_filter(
            FitnessEntry.session_id == session_id,
            current_user=current_user,
        )

    async def read_by_exercise_type(
        self,
        exercise_type: str,
        current_user: Any | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[FitnessEntryRead]:
        """Get fitness entries by exercise type with optional date filtering."""
        filter_condition = FitnessEntry.exercise_type == exercise_type

        if start_date:
            filter_condition &= FitnessEntry.activity_timestamp >= start_date
        if end_date:
            filter_condition &= FitnessEntry.activity_timestamp <= end_date

        return await self.read_multi_by_filter(
            filter_condition,
            current_user=current_user,
            offset=offset,
            limit=limit,
            order_by=FitnessEntry.activity_timestamp.desc(),
        )

    async def read_recent_entries(
        self,
        current_user: Any | None = None,
        days: int = 30,
        offset: int = 0,
        limit: int = 100,
    ) -> list[FitnessEntryRead]:
        """Get recent fitness entries."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        return await self.read_multi_by_filter(
            FitnessEntry.activity_timestamp >= cutoff_date,
            current_user=current_user,
            offset=offset,
            limit=limit,
            order_by=FitnessEntry.activity_timestamp.desc(),
        )


class RestDayEntryRepository(
    CRUDRepository[
        RestDayEntry,
        RestDayEntryCreate,
        RestDayEntryRead,
        RestDayEntryUpdate,
    ],
):
    """Repository for managing rest day entry operations."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the rest day entry repository."""
        super().__init__(
            model=RestDayEntry,
            create_schema=RestDayEntryCreate,
            read_schema=RestDayEntryRead,
            update_schema=RestDayEntryUpdate,
            session=session,
            not_found_exception=RestDayEntryNotFoundError,
            creation_exception=RestDayEntryCreationError,
            user_filter=self._user_filter,
        )

    def _user_filter(self, user: Any | None) -> Any:
        """Filter entries by user."""
        if user:
            return RestDayEntry.user_id == user.id
        return False

    async def read_by_rest_type(
        self,
        rest_type: str,
        current_user: Any | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[RestDayEntryRead]:
        """Get rest day entries by rest type."""
        return await self.read_multi_by_filter(
            RestDayEntry.rest_type == rest_type,
            current_user=current_user,
            offset=offset,
            limit=limit,
            order_by=RestDayEntry.activity_timestamp.desc(),
        )

    async def read_planned_vs_unplanned(
        self,
        current_user: Any | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict[str, int]:
        """Get count of planned vs unplanned rest days."""
        session = await self.get_session()

        filter_condition = self.user_filter(current_user)
        if start_date:
            filter_condition &= RestDayEntry.activity_timestamp >= start_date
        if end_date:
            filter_condition &= RestDayEntry.activity_timestamp <= end_date

        # Count planned rest days
        planned_result = await session.execute(
            select(func.count(RestDayEntry.id)).filter(
                filter_condition & (RestDayEntry.planned == True),
            ),
        )
        planned_count = planned_result.scalar() or 0

        # Count unplanned rest days
        unplanned_result = await session.execute(
            select(func.count(RestDayEntry.id)).filter(
                filter_condition & (RestDayEntry.planned == False),
            ),
        )
        unplanned_count = unplanned_result.scalar() or 0

        return {
            "planned": planned_count,
            "unplanned": unplanned_count,
            "total": planned_count + unplanned_count,
        }


class CricketCoachingEntryRepository(
    CRUDRepository[
        CricketCoachingEntry,
        CricketCoachingEntryCreate,
        CricketCoachingEntryRead,
        CricketCoachingEntryUpdate,
    ],
):
    """Repository for managing cricket coaching entry operations."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the cricket coaching entry repository."""
        super().__init__(
            model=CricketCoachingEntry,
            create_schema=CricketCoachingEntryCreate,
            read_schema=CricketCoachingEntryRead,
            update_schema=CricketCoachingEntryUpdate,
            session=session,
            not_found_exception=CricketCoachingEntryNotFoundError,
            creation_exception=CricketCoachingEntryCreationError,
            user_filter=self._user_filter,
        )

    def _user_filter(self, user: Any | None) -> Any:
        """Filter entries by user."""
        if user:
            return CricketCoachingEntry.user_id == user.id
        return False

    async def read_by_coach(
        self,
        coach_name: str,
        current_user: Any | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[CricketCoachingEntryRead]:
        """Get coaching entries by coach name."""
        return await self.read_multi_by_filter(
            CricketCoachingEntry.coach_name == coach_name,
            current_user=current_user,
            offset=offset,
            limit=limit,
            order_by=CricketCoachingEntry.activity_timestamp.desc(),
        )

    async def read_by_focus_area(
        self,
        focus_area: str,
        current_user: Any | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[CricketCoachingEntryRead]:
        """Get coaching entries by primary focus area."""
        return await self.read_multi_by_filter(
            CricketCoachingEntry.primary_focus == focus_area,
            current_user=current_user,
            offset=offset,
            limit=limit,
            order_by=CricketCoachingEntry.activity_timestamp.desc(),
        )

    async def read_by_discipline(
        self,
        discipline: str,
        current_user: Any | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[CricketCoachingEntryRead]:
        """Get coaching entries by discipline focus."""
        return await self.read_multi_by_filter(
            CricketCoachingEntry.discipline_focus == discipline,
            current_user=current_user,
            offset=offset,
            limit=limit,
            order_by=CricketCoachingEntry.activity_timestamp.desc(),
        )


class CricketMatchEntryRepository(
    CRUDRepository[
        CricketMatchEntry,
        CricketMatchEntryCreate,
        CricketMatchEntryRead,
        CricketMatchEntryUpdate,
    ],
):
    """Repository for managing cricket match entry operations."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the cricket match entry repository."""
        super().__init__(
            model=CricketMatchEntry,
            create_schema=CricketMatchEntryCreate,
            read_schema=CricketMatchEntryRead,
            update_schema=CricketMatchEntryUpdate,
            session=session,
            not_found_exception=CricketMatchEntryNotFoundError,
            creation_exception=CricketMatchEntryCreationError,
            user_filter=self._user_filter,
        )

    def _user_filter(self, user: Any | None) -> Any:
        """Filter entries by user."""
        if user:
            return CricketMatchEntry.user_id == user.id
        return False

    async def read_by_format(
        self,
        match_format: str,
        current_user: Any | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[CricketMatchEntryRead]:
        """Get match entries by format."""
        return await self.read_multi_by_filter(
            CricketMatchEntry.match_format == match_format,
            current_user=current_user,
            offset=offset,
            limit=limit,
            order_by=CricketMatchEntry.activity_timestamp.desc(),
        )

    async def read_by_result(
        self,
        result: str,
        current_user: Any | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[CricketMatchEntryRead]:
        """Get match entries by result."""
        return await self.read_multi_by_filter(
            CricketMatchEntry.result == result,
            current_user=current_user,
            offset=offset,
            limit=limit,
            order_by=CricketMatchEntry.activity_timestamp.desc(),
        )

    async def read_by_venue_type(
        self,
        venue_type: str,  # home, away, neutral
        current_user: Any | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[CricketMatchEntryRead]:
        """Get match entries by venue type."""
        return await self.read_multi_by_filter(
            CricketMatchEntry.home_away == venue_type,
            current_user=current_user,
            offset=offset,
            limit=limit,
            order_by=CricketMatchEntry.activity_timestamp.desc(),
        )

    async def get_performance_stats(
        self,
        current_user: Any | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict[str, Any]:
        """Get performance statistics."""
        session = await self.get_session()

        filter_condition = self.user_filter(current_user)
        if start_date:
            filter_condition &= CricketMatchEntry.activity_timestamp >= start_date
        if end_date:
            filter_condition &= CricketMatchEntry.activity_timestamp <= end_date

        # Get aggregated stats
        stats_result = await session.execute(
            select(
                func.count(CricketMatchEntry.id).label("total_matches"),
                func.sum(CricketMatchEntry.runs_scored).label("total_runs"),
                func.avg(CricketMatchEntry.runs_scored).label("avg_runs"),
                func.sum(CricketMatchEntry.wickets_taken).label("total_wickets"),
                func.avg(CricketMatchEntry.overall_performance).label("avg_performance"),
            ).filter(filter_condition),
        )

        stats = stats_result.first()

        # Count wins/losses
        results_query = await session.execute(
            select(CricketMatchEntry.result, func.count(CricketMatchEntry.id))
            .filter(filter_condition)
            .group_by(CricketMatchEntry.result),
        )

        results_breakdown = {result: count for result, count in results_query.all()}

        return {
            "total_matches": stats.total_matches or 0,
            "total_runs": int(stats.total_runs or 0),
            "average_runs": float(stats.avg_runs or 0),
            "total_wickets": int(stats.total_wickets or 0),
            "average_performance": float(stats.avg_performance or 0),
            "results_breakdown": results_breakdown,
        }
