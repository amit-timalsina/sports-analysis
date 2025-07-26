from collections.abc import AsyncGenerator
from datetime import datetime
from typing import Any

import svcs
from sqlalchemy import BinaryExpression, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from auth.schemas.user import User
from common.repositories.crud_repository import CRUDRepository
from fitness_tracking.exceptions import (
    CricketCoachingEntryCreationError,
    CricketCoachingEntryNotFoundError,
)
from fitness_tracking.models.cricket_coaching import CricketCoachingEntry
from fitness_tracking.schemas import (
    CricketCoachingEntryCreate,
    CricketCoachingEntryRead,
    CricketCoachingEntryUpdate,
)


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
            user_filter=self._user_filter,  # type: ignore[arg-type]
        )

    def _user_filter(self, user: User | None) -> BinaryExpression:  # type: ignore[return-value]
        """Filter entries by user."""
        if user:
            return CricketCoachingEntry.user_id == user.id  # type: ignore[return-value]
        return False  # type: ignore[return-value]

    async def read_by_coach(
        self,
        coach_name: str,
        current_user: User | None = None,
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
        current_user: User | None = None,
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
        current_user: User | None = None,
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

    async def get_coaching_stats(
        self,
        current_user: User | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict[str, Any]:
        """Get coaching statistics."""
        session = await self.get_session()

        filter_condition = self.user_filter(current_user)
        if start_date:
            filter_condition &= CricketCoachingEntry.activity_timestamp >= start_date
        if end_date:
            filter_condition &= CricketCoachingEntry.activity_timestamp <= end_date

        # Get aggregated stats
        stats_result = await session.execute(
            select(
                func.count(CricketCoachingEntry.id).label("total_coaching_sessions"),
                func.avg(CricketCoachingEntry.duration_minutes).label("avg_session_duration"),
                func.avg(CricketCoachingEntry.technique_rating).label("avg_technique_rating"),
                func.avg(CricketCoachingEntry.effort_level).label("avg_effort_level"),
            ).filter(filter_condition),
        )

        stats = stats_result.first()

        # Get focus areas distribution
        focus_query = await session.execute(
            select(CricketCoachingEntry.primary_focus, func.count(CricketCoachingEntry.id))
            .filter(filter_condition)
            .group_by(CricketCoachingEntry.primary_focus),
        )

        focus_breakdown = {focus: count for focus, count in focus_query.all()}

        # Get discipline distribution
        discipline_query = await session.execute(
            select(CricketCoachingEntry.discipline_focus, func.count(CricketCoachingEntry.id))
            .filter(filter_condition)
            .group_by(CricketCoachingEntry.discipline_focus),
        )

        discipline_breakdown = {discipline: count for discipline, count in discipline_query.all()}

        return {
            "total_coaching_sessions": stats.total_coaching_sessions if stats else 0,
            "average_session_duration": float(
                stats.avg_session_duration if stats and stats.avg_session_duration else 0,
            ),
            "average_self_assessment": float(
                stats.avg_technique_rating if stats and stats.avg_technique_rating else 0,
            ),  # Use technique_rating as self-assessment
            "average_coach_rating": float(
                stats.avg_effort_level if stats and stats.avg_effort_level else 0,
            ),  # Use effort_level as coach rating
            "focus_areas_breakdown": focus_breakdown,
            "discipline_breakdown": discipline_breakdown,
        }

    @classmethod
    async def get_as_dependency(
        cls,
        services: svcs.Container,
    ) -> AsyncGenerator["CricketCoachingEntryRepository", None]:
        """Get the cricket coaching entry repository as a dependency."""
        session = await services.aget(AsyncSession)
        yield CricketCoachingEntryRepository(session)
