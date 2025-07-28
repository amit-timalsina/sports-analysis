"""Test cases for fitness tracking repositories."""

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from fitness_tracking.models import (
    CricketMatchEntry,
    FitnessEntry,
)
from fitness_tracking.models.cricket_coaching import CricketCoachingEntry
from fitness_tracking.models.rest_day import RestDayEntry
from fitness_tracking.repositories.cricket_coaching_repository import CricketCoachingEntryRepository
from fitness_tracking.repositories.cricket_match_repository import (
    CricketMatchEntryRepository,
)
from fitness_tracking.repositories.fitness_repository import FitnessEntryRepository
from fitness_tracking.repositories.rest_day_repository import RestDayEntryRepository
from fitness_tracking.schemas import (
    CricketCoachingEntryRead,
    FitnessEntryRead,
    RestDayEntryRead,
)
from fitness_tracking.schemas.coaching_focus_type import (
    CoachingFocus,
)
from fitness_tracking.schemas.cricket_discipline_type import CricketDiscipline
from fitness_tracking.schemas.cricket_match import CricketMatchEntryRead
from fitness_tracking.schemas.exercise_type import ExerciseType
from fitness_tracking.schemas.intensity_level import IntensityLevel
from fitness_tracking.schemas.match_format import MatchFormat


@pytest.fixture
def mock_session() -> AsyncMock:
    """Create a mock async session."""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def mock_user() -> MagicMock:
    """Create a mock user."""
    user = MagicMock()
    user.id = "user123"
    return user


@pytest.fixture
def fitness_entry_repository(mock_session: AsyncMock) -> FitnessEntryRepository:
    """Create a fitness entry repository instance."""
    return FitnessEntryRepository(mock_session)


@pytest.fixture
def rest_day_repository(mock_session: AsyncMock) -> RestDayEntryRepository:
    """Create a rest day repository instance."""
    return RestDayEntryRepository(mock_session)


@pytest.fixture
def cricket_coaching_repository(mock_session: AsyncMock) -> CricketCoachingEntryRepository:
    """Create a cricket coaching repository instance."""
    return CricketCoachingEntryRepository(mock_session)


@pytest.fixture
def cricket_match_repository(mock_session: AsyncMock) -> CricketMatchEntryRepository:
    """Create a cricket match repository instance."""
    return CricketMatchEntryRepository(mock_session)


@pytest.fixture
def sample_fitness_entry() -> FitnessEntry:
    """Create a sample fitness entry."""
    return FitnessEntry(
        id=uuid.uuid4(),
        user_id="user123",
        session_id="session123",
        conversation_id=1,
        exercise_type=ExerciseType.CARDIO,
        exercise_name="Morning Run",
        duration_minutes=30,
        intensity=IntensityLevel.MODERATE,
        original_transcript="I went for a 30 minute run this morning",
        overall_confidence_score=0.95,
        mental_state="good",
        energy_level=7,
        notes="Felt great during the run",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


@pytest.fixture
def sample_rest_day_entry() -> RestDayEntry:
    """Create a sample rest day entry."""
    return RestDayEntry(
        id=uuid.uuid4(),
        user_id="user123",
        session_id="session123",
        conversation_id=2,
        rest_type="complete",
        planned=True,
        original_transcript="Taking a complete rest day today",
        overall_confidence_score=0.92,
        mental_state="relaxed",
        fatigue_level=3,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


@pytest.fixture
def sample_cricket_coaching_entry() -> CricketCoachingEntry:
    """Create a sample cricket coaching entry."""
    return CricketCoachingEntry(
        id=uuid.uuid4(),
        user_id="user123",
        session_id="session123",
        conversation_id=3,
        coach_name="Coach Smith",
        session_type="batting_drills",
        duration_minutes=60,
        primary_focus=CoachingFocus.TECHNIQUE,
        skills_practiced=["stance", "grip", "footwork"],
        discipline_focus=CricketDiscipline.BATTING,
        original_transcript="Had a 60 minute batting session with Coach Smith",
        overall_confidence_score=0.88,
        mental_state="focused",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


@pytest.fixture
def sample_cricket_match_entry() -> CricketMatchEntry:
    """Create a sample cricket match entry."""
    return CricketMatchEntry(
        id=uuid.uuid4(),
        user_id="user123",
        session_id="session123",
        conversation_id=4,
        match_format=MatchFormat.T20,
        opposition_team="Team A",
        venue="Home Ground",
        home_away="home",
        result="won",
        team_name="Our Team",
        runs_scored=45,
        wickets_taken=2,
        overall_performance=8,
        original_transcript="Played a T20 match today, scored 45 runs and took 2 wickets",
        overall_confidence_score=0.90,
        mental_state="excited",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


class TestFitnessEntryRepository:
    """Test cases for FitnessEntryRepository."""

    @pytest.mark.asyncio
    async def test_read_by_session_id(
        self,
        fitness_entry_repository: FitnessEntryRepository,
        mock_session: AsyncMock,
        sample_fitness_entry: FitnessEntry,
        mock_user: MagicMock,
    ) -> None:
        """Test reading fitness entries by session ID."""
        # Arrange
        session_id = "session123"

        # Create mock FitnessEntryRead instances
        mock_fitness_read = MagicMock(spec=FitnessEntryRead)
        mock_fitness_read.id = sample_fitness_entry.id
        mock_fitness_read.session_id = session_id
        mock_fitness_read.exercise_type = sample_fitness_entry.exercise_type

        # Mock the read_multi_by_filter method
        with patch.object(
            fitness_entry_repository,
            "read_multi_by_filter",
            return_value=[mock_fitness_read, mock_fitness_read],
        ) as mock_read:
            # Act
            result = await fitness_entry_repository.read_by_session_id(
                session_id,
                current_user=mock_user,
            )

            # Assert
            assert len(result) == 2
            assert all(entry.session_id == session_id for entry in result)
            mock_read.assert_called_once()

    @pytest.mark.asyncio
    async def test_read_by_exercise_type(
        self,
        fitness_entry_repository: FitnessEntryRepository,
        mock_session: AsyncMock,
        sample_fitness_entry: FitnessEntry,
        mock_user: MagicMock,
    ) -> None:
        """Test reading fitness entries by exercise type."""
        # Arrange
        exercise_type = "cardio"

        # Create mock FitnessEntryRead instance
        mock_fitness_read = MagicMock(spec=FitnessEntryRead)
        mock_fitness_read.id = sample_fitness_entry.id
        mock_fitness_read.exercise_type = exercise_type

        # Mock the read_multi_by_filter method
        with patch.object(
            fitness_entry_repository,
            "read_multi_by_filter",
            return_value=[mock_fitness_read],
        ) as mock_read:
            # Act
            result = await fitness_entry_repository.read_by_exercise_type(
                exercise_type,
                current_user=mock_user,
                start_date=datetime.now(UTC) - timedelta(days=7),
                end_date=datetime.now(UTC),
            )

            # Assert
            assert len(result) == 1
            assert result[0].exercise_type == exercise_type
            mock_read.assert_called_once()

    @pytest.mark.asyncio
    async def test_read_recent_entries(
        self,
        fitness_entry_repository: FitnessEntryRepository,
        mock_session: AsyncMock,
        sample_fitness_entry: FitnessEntry,
        mock_user: MagicMock,
    ) -> None:
        """Test reading recent fitness entries."""
        # Arrange
        # Create mock FitnessEntryRead instance
        mock_fitness_read = MagicMock(spec=FitnessEntryRead)
        mock_fitness_read.id = sample_fitness_entry.id
        mock_fitness_read.user_id = sample_fitness_entry.user_id

        # Mock the read_multi_by_filter method
        with patch.object(
            fitness_entry_repository,
            "read_multi_by_filter",
            return_value=[mock_fitness_read],
        ) as mock_read:
            # Act
            result = await fitness_entry_repository.read_recent_entries(
                current_user=mock_user,
                days=30,
                offset=0,
                limit=100,
            )

            # Assert
            assert len(result) == 1
            assert result[0].user_id == sample_fitness_entry.user_id
            mock_read.assert_called_once()


class TestRestDayEntryRepository:
    """Test cases for RestDayEntryRepository."""

    @pytest.mark.asyncio
    async def test_read_by_rest_type(
        self,
        rest_day_repository: RestDayEntryRepository,
        mock_session: AsyncMock,
        sample_rest_day_entry: RestDayEntry,
        mock_user: MagicMock,
    ) -> None:
        """Test reading rest day entries by rest type."""
        # Arrange
        rest_type = "complete"

        # Create a mock RestDayEntryRead instance
        mock_rest_day_read = MagicMock(spec=RestDayEntryRead)
        mock_rest_day_read.id = sample_rest_day_entry.id
        mock_rest_day_read.user_id = sample_rest_day_entry.user_id
        mock_rest_day_read.session_id = sample_rest_day_entry.session_id
        mock_rest_day_read.rest_type = sample_rest_day_entry.rest_type
        mock_rest_day_read.planned = sample_rest_day_entry.planned
        mock_rest_day_read.mental_state = sample_rest_day_entry.mental_state
        mock_rest_day_read.fatigue_level = sample_rest_day_entry.fatigue_level

        # Mock the read_multi_by_filter method
        with patch.object(
            rest_day_repository,
            "read_multi_by_filter",
            return_value=[mock_rest_day_read],
        ) as mock_read:
            # Act
            result = await rest_day_repository.read_by_rest_type(
                rest_type,
                current_user=mock_user,
            )

            # Assert
            assert len(result) == 1
            assert result[0].rest_type == rest_type
            mock_read.assert_called_once()

    @pytest.mark.asyncio
    async def test_read_planned_vs_unplanned(
        self,
        rest_day_repository: RestDayEntryRepository,
        mock_session: AsyncMock,
        mock_user: MagicMock,
    ) -> None:
        """Test getting planned vs unplanned rest days count."""
        # Arrange
        mock_result_planned = MagicMock()
        mock_result_planned.scalar.return_value = 5

        mock_result_unplanned = MagicMock()
        mock_result_unplanned.scalar.return_value = 3

        mock_session.execute = AsyncMock(
            side_effect=[mock_result_planned, mock_result_unplanned],
        )

        # Act
        result = await rest_day_repository.read_planned_vs_unplanned(
            current_user=mock_user,
            start_date=datetime.utcnow() - timedelta(days=30),
            end_date=datetime.utcnow(),
        )

        # Assert
        assert result["planned"] == 5
        assert result["unplanned"] == 3
        assert result["total"] == 8
        assert mock_session.execute.call_count == 2


class TestCricketCoachingEntryRepository:
    """Test cases for CricketCoachingEntryRepository."""

    @pytest.mark.asyncio
    async def test_read_by_coach(
        self,
        cricket_coaching_repository: CricketCoachingEntryRepository,
        mock_session: AsyncMock,
        sample_cricket_coaching_entry: CricketCoachingEntry,
        mock_user: MagicMock,
    ) -> None:
        """Test reading coaching entries by coach name."""
        # Arrange
        coach_name = "Coach Smith"

        # Create mock CricketCoachingEntryRead instance
        mock_coaching_read = MagicMock(spec=CricketCoachingEntryRead)
        mock_coaching_read.id = sample_cricket_coaching_entry.id
        mock_coaching_read.coach_name = coach_name

        # Mock the read_multi_by_filter method
        with patch.object(
            cricket_coaching_repository,
            "read_multi_by_filter",
            return_value=[mock_coaching_read],
        ) as mock_read:
            # Act
            result = await cricket_coaching_repository.read_by_coach(
                coach_name,
                current_user=mock_user,
            )

            # Assert
            assert len(result) == 1
            assert result[0].coach_name == coach_name
            mock_read.assert_called_once()

    @pytest.mark.asyncio
    async def test_read_by_focus_area(
        self,
        cricket_coaching_repository: CricketCoachingEntryRepository,
        mock_session: AsyncMock,
        sample_cricket_coaching_entry: CricketCoachingEntry,
        mock_user: MagicMock,
    ) -> None:
        """Test reading coaching entries by focus area."""
        # Arrange
        focus_area = "batting"

        # Create mock CricketCoachingEntryRead instance
        mock_coaching_read = MagicMock(spec=CricketCoachingEntryRead)
        mock_coaching_read.id = sample_cricket_coaching_entry.id
        mock_coaching_read.primary_focus = focus_area

        # Mock the read_multi_by_filter method
        with patch.object(
            cricket_coaching_repository,
            "read_multi_by_filter",
            return_value=[mock_coaching_read],
        ) as mock_read:
            # Act
            result = await cricket_coaching_repository.read_by_focus_area(
                focus_area,
                current_user=mock_user,
            )

            # Assert
            assert len(result) == 1
            assert result[0].primary_focus == focus_area
            mock_read.assert_called_once()

    @pytest.mark.asyncio
    async def test_read_by_discipline(
        self,
        cricket_coaching_repository: CricketCoachingEntryRepository,
        mock_session: AsyncMock,
        sample_cricket_coaching_entry: CricketCoachingEntry,
        mock_user: MagicMock,
    ) -> None:
        """Test reading coaching entries by discipline."""
        # Arrange
        discipline = "technique"

        # Create mock CricketCoachingEntryRead instance
        mock_coaching_read = MagicMock(spec=CricketCoachingEntryRead)
        mock_coaching_read.id = sample_cricket_coaching_entry.id
        mock_coaching_read.discipline_focus = discipline

        # Mock the read_multi_by_filter method
        with patch.object(
            cricket_coaching_repository,
            "read_multi_by_filter",
            return_value=[mock_coaching_read],
        ) as mock_read:
            # Act
            result = await cricket_coaching_repository.read_by_discipline(
                discipline,
                current_user=mock_user,
            )

            # Assert
            assert len(result) == 1
            assert result[0].discipline_focus == discipline
            mock_read.assert_called_once()


class TestCricketMatchEntryRepository:
    """Test cases for CricketMatchEntryRepository."""

    @pytest.mark.asyncio
    async def test_read_by_format(
        self,
        cricket_match_repository: CricketMatchEntryRepository,
        mock_session: AsyncMock,
        sample_cricket_match_entry: CricketMatchEntry,
        mock_user: MagicMock,
    ) -> None:
        """Test reading match entries by format."""
        # Arrange
        match_format = "T20"

        # Create mock CricketMatchEntryRead instance
        mock_match_read = MagicMock(spec=CricketMatchEntryRead)
        mock_match_read.id = sample_cricket_match_entry.id
        mock_match_read.match_format = match_format

        # Mock the read_multi_by_filter method
        with patch.object(
            cricket_match_repository,
            "read_multi_by_filter",
            return_value=[mock_match_read],
        ) as mock_read:
            # Act
            result = await cricket_match_repository.read_by_format(
                match_format,
                current_user=mock_user,
            )

            # Assert
            assert len(result) == 1
            assert result[0].match_format == match_format
            mock_read.assert_called_once()

    @pytest.mark.asyncio
    async def test_read_by_result(
        self,
        cricket_match_repository: CricketMatchEntryRepository,
        mock_session: AsyncMock,
        sample_cricket_match_entry: CricketMatchEntry,
        mock_user: MagicMock,
    ) -> None:
        """Test reading match entries by result."""
        # Arrange
        result_type = "won"

        # Create mock CricketMatchEntryRead instance
        mock_match_read = MagicMock(spec=CricketMatchEntryRead)
        mock_match_read.id = sample_cricket_match_entry.id
        mock_match_read.result = result_type

        # Mock the read_multi_by_filter method
        with patch.object(
            cricket_match_repository,
            "read_multi_by_filter",
            return_value=[mock_match_read],
        ) as mock_read:
            # Act
            results = await cricket_match_repository.read_by_result(
                result_type,
                current_user=mock_user,
            )

            # Assert
            assert len(results) == 1
            assert results[0].result == result_type
            mock_read.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_performance_stats(
        self,
        cricket_match_repository: CricketMatchEntryRepository,
        mock_session: AsyncMock,
        mock_user: MagicMock,
    ) -> None:
        """Test getting performance statistics."""
        # Arrange
        # Mock aggregated stats
        mock_stats = MagicMock()
        mock_stats.total_matches = 10
        mock_stats.total_runs = 350
        mock_stats.avg_runs = 35.0
        mock_stats.total_wickets = 15
        mock_stats.avg_performance = 7.5

        mock_stats_result = MagicMock()
        mock_stats_result.first.return_value = mock_stats

        # Mock results breakdown
        mock_results_query = MagicMock()
        mock_results_query.all.return_value = [("won", 6), ("lost", 3), ("draw", 1)]

        mock_session.execute = AsyncMock(
            side_effect=[mock_stats_result, mock_results_query],
        )

        # Act
        result = await cricket_match_repository.get_performance_stats(
            current_user=mock_user,
            start_date=datetime.utcnow() - timedelta(days=30),
            end_date=datetime.utcnow(),
        )

        # Assert
        assert result["total_matches"] == 10
        assert result["total_runs"] == 350
        assert result["average_runs"] == 35.0
        assert result["total_wickets"] == 15
        assert result["average_performance"] == 7.5
        assert result["results_breakdown"]["won"] == 6
        assert result["results_breakdown"]["lost"] == 3
        assert result["results_breakdown"]["draw"] == 1
        assert mock_session.execute.call_count == 2
