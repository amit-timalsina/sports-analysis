from collections.abc import AsyncGenerator
from datetime import datetime
from typing import Any

import svcs
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from auth.schemas.user import User
from common.repositories.crud_repository import CRUDRepository
from fitness_tracking.exceptions import RestDayEntryCreationError, RestDayEntryNotFoundError
from fitness_tracking.models.rest_day import RestDayEntry
from fitness_tracking.schemas import RestDayEntryCreate, RestDayEntryRead, RestDayEntryUpdate


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
            user_filter=self._user_filter,  # type: ignore[arg-type]
        )

    def _user_filter(self, user: User | None) -> bool:
        """Filter entries by user."""
        if user:
            return RestDayEntry.user_id == user.id  # type: ignore[return-value]
        return False

    async def read_by_rest_type(
        self,
        rest_type: str,
        current_user: User | None = None,
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
        current_user: User | None = None,
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
                filter_condition & (RestDayEntry.planned),
            ),
        )
        planned_count = planned_result.scalar() or 0

        # Count unplanned rest days
        unplanned_result = await session.execute(
            select(func.count(RestDayEntry.id)).filter(
                filter_condition & (not RestDayEntry.planned),
            ),
        )
        unplanned_count = unplanned_result.scalar() or 0

        return {
            "planned": planned_count,
            "unplanned": unplanned_count,
            "total": planned_count + unplanned_count,
        }

    async def get_rest_stats(
        self,
        current_user: User | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict[str, Any]:
        """Get rest day statistics."""
        session = await self.get_session()

        filter_condition = self.user_filter(current_user)
        if start_date:
            filter_condition &= RestDayEntry.activity_timestamp >= start_date
        if end_date:
            filter_condition &= RestDayEntry.activity_timestamp <= end_date

        # Get aggregated stats
        stats_result = await session.execute(
            select(
                func.count(RestDayEntry.id).label("total_rest_days"),
                func.avg(RestDayEntry.sleep_hours).label("avg_sleep_hours"),
                func.avg(RestDayEntry.sleep_quality).label("avg_sleep_quality"),
                func.avg(RestDayEntry.recovery_score).label("avg_recovery_score"),
                func.avg(RestDayEntry.readiness_for_next_workout).label("avg_readiness"),
            ).filter(filter_condition),
        )

        stats = stats_result.first()

        # Get rest type distribution
        rest_type_query = await session.execute(
            select(RestDayEntry.rest_type, func.count(RestDayEntry.id))
            .filter(filter_condition)
            .group_by(RestDayEntry.rest_type),
        )

        rest_type_breakdown = {rest_type: count for rest_type, count in rest_type_query.all()}

        # Get planned vs unplanned breakdown
        planned_query = await session.execute(
            select(RestDayEntry.planned, func.count(RestDayEntry.id))
            .filter(filter_condition)
            .group_by(RestDayEntry.planned),
        )

        planned_breakdown = {str(planned): count for planned, count in planned_query.all()}

        return {
            "total_rest_days": stats.total_rest_days if stats else 0,
            "average_sleep_hours": float(
                stats.avg_sleep_hours if stats and stats.avg_sleep_hours else 0
            ),
            "average_sleep_quality": float(
                stats.avg_sleep_quality if stats and stats.avg_sleep_quality else 0
            ),
            "average_recovery_score": float(
                stats.avg_recovery_score if stats and stats.avg_recovery_score else 0
            ),
            "average_readiness": float(stats.avg_readiness if stats and stats.avg_readiness else 0),
            "rest_type_breakdown": rest_type_breakdown,
            "planned_breakdown": planned_breakdown,
        }

    @classmethod
    async def get_as_dependency(
        cls,
        services: svcs.Container,
    ) -> AsyncGenerator["RestDayEntryRepository", None]:
        """Get the rest day entry repository as a dependency."""
        session = await services.aget(AsyncSession)
        yield RestDayEntryRepository(session)
