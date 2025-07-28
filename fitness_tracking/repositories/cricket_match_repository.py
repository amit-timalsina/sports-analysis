from collections.abc import AsyncGenerator
from datetime import datetime
from typing import Any

import svcs
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from auth.schemas.user import User
from common.repositories.crud_repository import CRUDRepository
from fitness_tracking.exceptions import (
    CricketMatchEntryCreationError,
    CricketMatchEntryNotFoundError,
)
from fitness_tracking.models import CricketMatchEntry
from fitness_tracking.schemas.cricket_match import (
    CricketMatchEntryCreate,
    CricketMatchEntryRead,
    CricketMatchEntryUpdate,
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
            user_filter=self._user_filter,  # type: ignore[arg-type]
        )

    def _user_filter(self, user: User | None) -> bool:
        """Filter entries by user."""
        if user:
            return CricketMatchEntry.user_id == user.id  # type: ignore[return-value]
        return False

    async def read_by_format(
        self,
        match_format: str,
        current_user: User | None = None,
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
        current_user: User | None = None,
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
        current_user: User | None = None,
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
        current_user: User | None = None,
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

    @classmethod
    async def get_as_dependency(
        cls,
        services: svcs.Container,
    ) -> AsyncGenerator["CricketMatchEntryRepository", None]:
        """Get the cricket match entry repository as a dependency."""
        session = await services.aget(AsyncSession)
        yield CricketMatchEntryRepository(session)
