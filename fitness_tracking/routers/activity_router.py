"""Activity routers for fitness tracking API endpoints."""

from uuid import UUID

import svcs
from fastapi import APIRouter

# Note: These imports would need to be updated based on your auth system
# from auth.dependencies.security import get_current_user
# from auth.schemas.user import User as UserGet
from fitness_tracking.exceptions import (
    CricketCoachingEntryCreationError,
    CricketMatchEntryCreationError,
    FitnessEntryCreationError,
    FitnessEntryNotFoundError,
    RestDayEntryCreationError,
    RestDayEntryNotFoundError,
)
from fitness_tracking.repositories.cricket_coaching_repository import CricketCoachingEntryRepository
from fitness_tracking.repositories.cricket_match_repository import (
    CricketMatchEntryRepository,
)
from fitness_tracking.repositories.fitness_repository import FitnessEntryRepository
from fitness_tracking.repositories.rest_day_repository import RestDayEntryRepository
from fitness_tracking.schemas import (
    CricketCoachingEntryCreate,
    CricketCoachingEntryRead,
    FitnessEntryCreate,
    FitnessEntryRead,
    FitnessEntryUpdate,
    RestDayEntryCreate,
    RestDayEntryRead,
)
from fitness_tracking.schemas.cricket_match import CricketMatchEntryCreate, CricketMatchEntryRead

# Initialize routers
fitness_router = APIRouter(prefix="/fitness", tags=["fitness"])
rest_day_router = APIRouter(prefix="/rest-days", tags=["rest-days"])
cricket_coaching_router = APIRouter(prefix="/cricket/coaching", tags=["cricket-coaching"])
cricket_match_router = APIRouter(prefix="/cricket/matches", tags=["cricket-matches"])


# Fitness Entry Endpoints
@fitness_router.post("", response_model=FitnessEntryRead)
async def create_fitness_entry(
    entry: FitnessEntryCreate,
    dep_container: svcs.fastapi.DepContainer,
    # current_user: Annotated[UserGet, Depends(get_current_user)],
) -> FitnessEntryRead:
    """Create a new fitness entry."""
    repository = await dep_container.aget(FitnessEntryRepository)

    try:
        return await repository.create(entry)  # , current_user)
    except FitnessEntryCreationError as e:
        raise e.to_http_exception() from None


@fitness_router.get("", response_model=list[FitnessEntryRead])
async def read_fitness_entries(
    dep_container: svcs.fastapi.DepContainer,
    # current_user: Annotated[UserGet, Depends(get_current_user)],
    offset: int = 0,
    limit: int = 100,
) -> list[FitnessEntryRead]:
    """Get fitness entries."""
    repository = await dep_container.aget(FitnessEntryRepository)
    return await repository.read_multi(offset=offset, limit=limit)  # current_user=current_user


@fitness_router.get("/{entry_id}", response_model=FitnessEntryRead)
async def read_fitness_entry(
    entry_id: UUID,
    dep_container: svcs.fastapi.DepContainer,
    # current_user: Annotated[UserGet, Depends(get_current_user)],
) -> FitnessEntryRead:
    """Get a specific fitness entry."""
    repository = await dep_container.aget(FitnessEntryRepository)

    try:
        return await repository.read(entry_id)  # , current_user)
    except FitnessEntryNotFoundError as e:
        raise e.to_http_exception() from None


@fitness_router.put("/{entry_id}", response_model=FitnessEntryRead)
async def update_fitness_entry(
    entry_id: UUID,
    entry_update: FitnessEntryUpdate,
    dep_container: svcs.fastapi.DepContainer,
    # current_user: Annotated[UserGet, Depends(get_current_user)],
) -> FitnessEntryRead:
    """Update a fitness entry."""
    repository = await dep_container.aget(FitnessEntryRepository)

    try:
        return await repository.update(entry_id, entry_update)  # , current_user)
    except FitnessEntryNotFoundError as e:
        raise e.to_http_exception() from None


@fitness_router.delete("/{entry_id}")
async def delete_fitness_entry(
    entry_id: UUID,
    dep_container: svcs.fastapi.DepContainer,
    # current_user: Annotated[UserGet, Depends(get_current_user)],
) -> FitnessEntryRead:
    """Delete a fitness entry."""
    repository = await dep_container.aget(FitnessEntryRepository)

    try:
        return await repository.delete(entry_id)  # , current_user)
    except FitnessEntryNotFoundError as e:
        raise e.to_http_exception() from None


@fitness_router.get("/by-exercise-type/{exercise_type}", response_model=list[FitnessEntryRead])
async def read_fitness_entries_by_type(
    exercise_type: str,
    dep_container: svcs.fastapi.DepContainer,
    # current_user: Annotated[UserGet, Depends(get_current_user)],
    offset: int = 0,
    limit: int = 100,
) -> list[FitnessEntryRead]:
    """Get fitness entries by exercise type."""
    repository = await dep_container.aget(FitnessEntryRepository)
    return await repository.read_by_exercise_type(
        exercise_type,
        offset=offset,
        limit=limit,
    )  # current_user=current_user


# Rest Day Entry Endpoints
@rest_day_router.post("", response_model=RestDayEntryRead)
async def create_rest_day_entry(
    entry: RestDayEntryCreate,
    dep_container: svcs.fastapi.DepContainer,
    # current_user: Annotated[UserGet, Depends(get_current_user)],
) -> RestDayEntryRead:
    """Create a new rest day entry."""
    repository = await dep_container.aget(RestDayEntryRepository)

    try:
        return await repository.create(entry)  # , current_user)
    except RestDayEntryCreationError as e:
        raise e.to_http_exception() from None


@rest_day_router.get("", response_model=list[RestDayEntryRead])
async def read_rest_day_entries(
    dep_container: svcs.fastapi.DepContainer,
    # current_user: Annotated[UserGet, Depends(get_current_user)],
    offset: int = 0,
    limit: int = 100,
) -> list[RestDayEntryRead]:
    """Get rest day entries."""
    repository = await dep_container.aget(RestDayEntryRepository)
    return await repository.read_multi(offset=offset, limit=limit)  # current_user=current_user


@rest_day_router.get("/{entry_id}", response_model=RestDayEntryRead)
async def read_rest_day_entry(
    entry_id: UUID,
    dep_container: svcs.fastapi.DepContainer,
    # current_user: Annotated[UserGet, Depends(get_current_user)],
) -> RestDayEntryRead:
    """Get a specific rest day entry."""
    repository = await dep_container.aget(RestDayEntryRepository)

    try:
        return await repository.read(entry_id)  # , current_user)
    except RestDayEntryNotFoundError as e:
        raise e.to_http_exception() from None


# Cricket Coaching Entry Endpoints
@cricket_coaching_router.post("", response_model=CricketCoachingEntryRead)
async def create_cricket_coaching_entry(
    entry: CricketCoachingEntryCreate,
    dep_container: svcs.fastapi.DepContainer,
    # current_user: Annotated[UserGet, Depends(get_current_user)],
) -> CricketCoachingEntryRead:
    """Create a new cricket coaching entry."""
    repository = await dep_container.aget(CricketCoachingEntryRepository)

    try:
        return await repository.create(entry)  # , current_user)
    except CricketCoachingEntryCreationError as e:
        raise e.to_http_exception() from None


@cricket_coaching_router.get("", response_model=list[CricketCoachingEntryRead])
async def read_cricket_coaching_entries(
    dep_container: svcs.fastapi.DepContainer,
    # current_user: Annotated[UserGet, Depends(get_current_user)],
    offset: int = 0,
    limit: int = 100,
) -> list[CricketCoachingEntryRead]:
    """Get cricket coaching entries."""
    repository = await dep_container.aget(CricketCoachingEntryRepository)
    return await repository.read_multi(offset=offset, limit=limit)  # current_user=current_user


@cricket_coaching_router.get(
    "/by-coach/{coach_name}",
    response_model=list[CricketCoachingEntryRead],
)
async def read_coaching_entries_by_coach(
    coach_name: str,
    dep_container: svcs.fastapi.DepContainer,
    # current_user: Annotated[UserGet, Depends(get_current_user)],
    offset: int = 0,
    limit: int = 100,
) -> list[CricketCoachingEntryRead]:
    """Get coaching entries by coach name."""
    repository = await dep_container.aget(CricketCoachingEntryRepository)
    return await repository.read_by_coach(
        coach_name,
        offset=offset,
        limit=limit,
    )  # current_user=current_user


# Cricket Match Entry Endpoints
@cricket_match_router.post("", response_model=CricketMatchEntryRead)
async def create_cricket_match_entry(
    entry: CricketMatchEntryCreate,
    dep_container: svcs.fastapi.DepContainer,
    # current_user: Annotated[UserGet, Depends(get_current_user)],
) -> CricketMatchEntryRead:
    """Create a new cricket match entry."""
    repository = await dep_container.aget(CricketMatchEntryRepository)

    try:
        return await repository.create(entry)  # , current_user)
    except CricketMatchEntryCreationError as e:
        raise e.to_http_exception() from None


@cricket_match_router.get("", response_model=list[CricketMatchEntryRead])
async def read_cricket_match_entries(
    dep_container: svcs.fastapi.DepContainer,
    # current_user: Annotated[UserGet, Depends(get_current_user)],
    offset: int = 0,
    limit: int = 100,
) -> list[CricketMatchEntryRead]:
    """Get cricket match entries."""
    repository = await dep_container.aget(CricketMatchEntryRepository)
    return await repository.read_multi(offset=offset, limit=limit)  # current_user=current_user


@cricket_match_router.get("/stats", response_model=dict)
async def get_cricket_match_stats(
    dep_container: svcs.fastapi.DepContainer,
    # current_user: Annotated[UserGet, Depends(get_current_user)],
) -> dict:
    """Get cricket match performance statistics."""
    repository = await dep_container.aget(CricketMatchEntryRepository)
    return await repository.get_performance_stats()  # current_user=current_user


@cricket_match_router.get("/by-format/{match_format}", response_model=list[CricketMatchEntryRead])
async def read_match_entries_by_format(
    match_format: str,
    dep_container: svcs.fastapi.DepContainer,
    # current_user: Annotated[UserGet, Depends(get_current_user)],
    offset: int = 0,
    limit: int = 100,
) -> list[CricketMatchEntryRead]:
    """Get match entries by format."""
    repository = await dep_container.aget(CricketMatchEntryRepository)
    return await repository.read_by_format(
        match_format,
        offset=offset,
        limit=limit,
    )  # current_user=current_user
