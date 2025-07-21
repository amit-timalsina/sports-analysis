from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta

import svcs
from sqlalchemy.ext.asyncio import AsyncSession

from auth.schemas.user import User
from common.repositories.crud_repository import CRUDRepository
from fitness_tracking.exceptions import FitnessEntryCreationError, FitnessEntryNotFoundError
from fitness_tracking.models import FitnessEntry
from fitness_tracking.schemas import FitnessEntryCreate, FitnessEntryRead, FitnessEntryUpdate


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
            user_filter=self._user_filter,  # type: ignore[arg-type]
        )

    def _user_filter(self, user: User | None) -> bool:
        """Filter notifications to only show those for the current user."""
        if user:
            return FitnessEntry.user_id == user.id  # type: ignore[return-value]
        return False

    async def read_by_session_id(
        self,
        session_id: str,
        current_user: User | None = None,
    ) -> list[FitnessEntryRead]:
        """Get fitness entries by session ID."""
        return await self.read_multi_by_filter(
            FitnessEntry.session_id == session_id,
            current_user=current_user,
        )

    async def read_by_exercise_type(  # noqa: PLR0913
        self,
        exercise_type: str,
        current_user: User | None = None,
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
        current_user: User | None = None,
        days: int = 30,
        offset: int = 0,
        limit: int = 100,
    ) -> list[FitnessEntryRead]:
        """Get recent fitness entries."""
        cutoff_date = datetime.now(UTC) - timedelta(days=days)
        return await self.read_multi_by_filter(
            FitnessEntry.activity_timestamp >= cutoff_date,
            current_user=current_user,
            offset=offset,
            limit=limit,
            order_by=FitnessEntry.activity_timestamp.desc(),
        )

    @classmethod
    async def get_as_dependency(
        cls,
        services: svcs.Container,
    ) -> AsyncGenerator["FitnessEntryRepository", None]:
        """Get the fitness entry repository as a dependency."""
        session = await services.aget(AsyncSession)
        yield FitnessEntryRepository(session)
