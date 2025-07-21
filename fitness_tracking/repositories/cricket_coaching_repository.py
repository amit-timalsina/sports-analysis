from collections.abc import AsyncGenerator

import svcs
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

    def _user_filter(self, user: User | None) -> bool:
        """Filter entries by user."""
        if user:
            return CricketCoachingEntry.user_id == user.id  # type: ignore[return-value]
        return False

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

    @classmethod
    async def get_as_dependency(
        cls,
        services: svcs.Container,
    ) -> AsyncGenerator["CricketCoachingEntryRepository", None]:
        """Get the cricket coaching entry repository as a dependency."""
        session = await services.aget(AsyncSession)
        yield CricketCoachingEntryRepository(session)
