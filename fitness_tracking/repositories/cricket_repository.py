"""Cricket repositories with analytics capabilities."""

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from common.exceptions import AppError
from common.repositories.base_repository import BaseRepository
from fitness_tracking.models.cricket import (
    CricketCoachingEntry,
    CricketMatchEntry,
    CricketSessionType,
    MatchType,
    RestDayEntry,
    RestType,
)
from fitness_tracking.schemas.cricket import (
    CricketAnalytics,
    CricketCoachingDataExtraction,
    CricketCoachingEntryCreate,
    CricketCoachingEntryRead,
    CricketCoachingEntryUpdate,
    CricketMatchDataExtraction,
    CricketMatchEntryCreate,
    CricketMatchEntryRead,
    CricketMatchEntryUpdate,
    RestDayDataExtraction,
    RestDayEntryCreate,
    RestDayEntryRead,
    RestDayEntryUpdate,
)

logger = logging.getLogger(__name__)


class CricketRepositoryError(AppError):
    """Cricket repository specific error."""

    status_code = 500
    detail = "Cricket repository operation failed"


class CricketCoachingRepository(
    BaseRepository[
        CricketCoachingEntry,
        CricketCoachingEntryCreate,
        CricketCoachingEntryRead,
        CricketCoachingEntryUpdate,
    ],
):
    """Repository for cricket coaching session operations."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize cricket coaching repository."""
        super().__init__(CricketCoachingEntry, session)

    def _normalize_session_type(self, session_type: str) -> CricketSessionType:
        """Normalize session type strings to valid CricketSessionType enum values."""
        session_type_lower = session_type.lower().strip()

        # Mapping of common variations to valid enum values
        session_type_mapping = {
            # Batting variations
            "batting": CricketSessionType.BATTING_DRILLS,
            "batting_drills": CricketSessionType.BATTING_DRILLS,
            "batting drills": CricketSessionType.BATTING_DRILLS,
            "batting practice": CricketSessionType.BATTING_DRILLS,
            "bat": CricketSessionType.BATTING_DRILLS,
            "stroke play": CricketSessionType.BATTING_DRILLS,
            "technique": CricketSessionType.BATTING_DRILLS,
            # Wicket keeping variations
            "keeping": CricketSessionType.WICKET_KEEPING,
            "wicket_keeping": CricketSessionType.WICKET_KEEPING,
            "wicket keeping": CricketSessionType.WICKET_KEEPING,
            "wicketkeeping": CricketSessionType.WICKET_KEEPING,
            "gloves": CricketSessionType.WICKET_KEEPING,
            "keeper": CricketSessionType.WICKET_KEEPING,
            # Netting variations
            "nets": CricketSessionType.NETTING,
            "netting": CricketSessionType.NETTING,
            "net session": CricketSessionType.NETTING,
            "net practice": CricketSessionType.NETTING,
            # Personal coaching variations
            "personal": CricketSessionType.PERSONAL_COACHING,
            "personal_coaching": CricketSessionType.PERSONAL_COACHING,
            "personal coaching": CricketSessionType.PERSONAL_COACHING,
            "1-on-1": CricketSessionType.PERSONAL_COACHING,
            "one on one": CricketSessionType.PERSONAL_COACHING,
            "individual": CricketSessionType.PERSONAL_COACHING,
            "private": CricketSessionType.PERSONAL_COACHING,
            # Team practice variations
            "team": CricketSessionType.TEAM_PRACTICE,
            "team_practice": CricketSessionType.TEAM_PRACTICE,
            "team practice": CricketSessionType.TEAM_PRACTICE,
            "squad": CricketSessionType.TEAM_PRACTICE,
            "group": CricketSessionType.TEAM_PRACTICE,
            "training": CricketSessionType.TEAM_PRACTICE,
            # Other/general variations
            "other": CricketSessionType.OTHER,
            "general": CricketSessionType.OTHER,
            "mixed": CricketSessionType.OTHER,
            "various": CricketSessionType.OTHER,
        }

        normalized = session_type_mapping.get(session_type_lower)
        if normalized:
            return normalized

        # Try partial matching for compound terms
        if any(keyword in session_type_lower for keyword in ["batting", "bat", "stroke"]):
            return CricketSessionType.BATTING_DRILLS
        if any(keyword in session_type_lower for keyword in ["keeping", "keeper", "glove"]):
            return CricketSessionType.WICKET_KEEPING
        if any(keyword in session_type_lower for keyword in ["net", "practice"]):
            return CricketSessionType.NETTING
        if any(keyword in session_type_lower for keyword in ["team", "squad", "group"]):
            return CricketSessionType.TEAM_PRACTICE
        if any(keyword in session_type_lower for keyword in ["personal", "individual", "private"]):
            return CricketSessionType.PERSONAL_COACHING

        # Default fallback
        logger.warning("Unknown session type '%s', defaulting to 'other'", session_type)
        return CricketSessionType.OTHER

    async def create_from_voice_data(
        self,
        session_id: str,
        user_id: str,
        voice_data: CricketCoachingDataExtraction | dict[str, Any],
        transcript: str,
        confidence_score: float,
        processing_duration: float,
    ) -> CricketCoachingEntry:
        """Create cricket coaching entry from voice processing data."""
        try:
            # Handle both Pydantic model and dict input
            if isinstance(voice_data, CricketCoachingDataExtraction):
                data = voice_data.model_dump()
            else:
                data = voice_data

            # Normalize session type
            session_type = self._normalize_session_type(data.get("session_type", "other"))

            # Create cricket coaching entry
            coaching_entry = CricketCoachingEntry(
                session_id=session_id,
                user_id=user_id,
                # Voice processing metadata
                transcript=transcript,
                confidence_score=confidence_score,
                processing_duration=processing_duration,
                # Cricket coaching data
                session_type=session_type,
                duration_minutes=data.get("duration_minutes", 30),
                what_went_well=data.get("what_went_well", ""),
                areas_for_improvement=data.get("areas_for_improvement", ""),
                coach_feedback=data.get("coach_feedback"),
                self_assessment_score=data.get("self_assessment_score", 5),
                skills_practiced=data.get("skills_practiced", ""),
                difficulty_level=data.get("difficulty_level", 5),
                confidence_level=data.get("confidence_level", 5),
                focus_level=data.get("focus_level", 5),
                learning_satisfaction=data.get("learning_satisfaction", 5),
                mental_state=data.get("mental_state", "good"),
                notes=data.get("notes"),
            )

            self.session.add(coaching_entry)
            await self.session.commit()
            await self.session.refresh(coaching_entry)

            logger.info("Created cricket coaching entry from voice data: %s", coaching_entry.id)
            return coaching_entry

        except Exception as e:
            await self.session.rollback()
            logger.exception("Failed to create cricket coaching entry from voice data")
            msg = f"Failed to create cricket coaching entry: {e}"
            raise CricketRepositoryError(msg) from e

    def _to_read_schema(self, db_record: CricketCoachingEntry) -> CricketCoachingEntryRead:
        """Convert database model to read schema."""
        return CricketCoachingEntryRead(
            id=db_record.id,
            session_id=db_record.session_id,
            user_id=db_record.user_id,
            session_type=db_record.session_type.value,
            duration_minutes=db_record.duration_minutes,
            what_went_well=db_record.what_went_well,
            areas_for_improvement=db_record.areas_for_improvement,
            skills_practiced=db_record.skills_practiced,
            self_assessment_score=db_record.self_assessment_score,
            confidence_level=db_record.confidence_level,
            focus_level=db_record.focus_level,
            mental_state=db_record.mental_state,
            coach_feedback=db_record.coach_feedback,
            difficulty_level=db_record.difficulty_level,
            learning_satisfaction=db_record.learning_satisfaction,
            notes=db_record.notes,
            transcript=db_record.transcript,
            confidence_score=db_record.confidence_score,
            processing_duration=db_record.processing_duration,
            created_at=db_record.created_at,
            updated_at=db_record.updated_at,
        )


class CricketMatchRepository(
    BaseRepository[
        CricketMatchEntry,
        CricketMatchEntryCreate,
        CricketMatchEntryRead,
        CricketMatchEntryUpdate,
    ],
):
    """Repository for cricket match performance operations."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize cricket match repository."""
        super().__init__(CricketMatchEntry, session)

    def _normalize_match_type(self, match_type: str) -> MatchType:
        """Normalize match type strings to valid MatchType enum values."""
        match_type_lower = match_type.lower().strip()

        # Mapping of common variations to valid enum values
        match_type_mapping = {
            # Practice variations
            "practice": MatchType.PRACTICE,
            "practice match": MatchType.PRACTICE,
            "friendly": MatchType.PRACTICE,
            "warm up": MatchType.PRACTICE,
            "warmup": MatchType.PRACTICE,
            "trial": MatchType.PRACTICE,
            # Tournament variations
            "tournament": MatchType.TOURNAMENT,
            "competition": MatchType.TOURNAMENT,
            "championship": MatchType.TOURNAMENT,
            "cup": MatchType.TOURNAMENT,
            "final": MatchType.TOURNAMENT,
            "semi-final": MatchType.TOURNAMENT,
            "quarter-final": MatchType.TOURNAMENT,
            "playoff": MatchType.TOURNAMENT,
            # International/Professional formats (map to tournament)
            "odi": MatchType.TOURNAMENT,
            "one day": MatchType.TOURNAMENT,
            "one-day": MatchType.TOURNAMENT,
            "t20": MatchType.TOURNAMENT,
            "twenty20": MatchType.TOURNAMENT,
            "test": MatchType.TOURNAMENT,
            "test match": MatchType.TOURNAMENT,
            "international": MatchType.TOURNAMENT,
            "domestic": MatchType.TOURNAMENT,
            "first class": MatchType.TOURNAMENT,
            "list a": MatchType.TOURNAMENT,
            # School variations
            "school": MatchType.SCHOOL,
            "inter school": MatchType.SCHOOL,
            "inter-school": MatchType.SCHOOL,
            "school team": MatchType.SCHOOL,
            "college": MatchType.SCHOOL,
            "university": MatchType.SCHOOL,
            "academic": MatchType.SCHOOL,
            # Club variations
            "club": MatchType.CLUB,
            "club match": MatchType.CLUB,
            "local": MatchType.CLUB,
            "community": MatchType.CLUB,
            "recreational": MatchType.CLUB,
            "league": MatchType.CLUB,
            "district": MatchType.CLUB,
            "regional": MatchType.CLUB,
            # Other variations
            "other": MatchType.OTHER,
            "casual": MatchType.OTHER,
            "social": MatchType.OTHER,
            "exhibition": MatchType.OTHER,
        }

        normalized = match_type_mapping.get(match_type_lower)
        if normalized:
            return normalized

        # Try partial matching for compound terms
        if any(
            keyword in match_type_lower for keyword in ["practice", "friendly", "warm", "trial"]
        ):
            return MatchType.PRACTICE
        if any(
            keyword in match_type_lower
            for keyword in ["tournament", "competition", "cup", "final", "championship"]
        ) or any(
            keyword in match_type_lower
            for keyword in ["odi", "t20", "test", "international", "first class"]
        ):
            return MatchType.TOURNAMENT
        if any(
            keyword in match_type_lower
            for keyword in ["school", "college", "university", "academic"]
        ):
            return MatchType.SCHOOL
        if any(
            keyword in match_type_lower
            for keyword in ["club", "local", "community", "league", "district"]
        ):
            return MatchType.CLUB

        # Default fallback
        logger.warning("Unknown match type '%s', defaulting to 'other'", match_type)
        return MatchType.OTHER

    async def create_from_voice_data(
        self,
        session_id: str,
        user_id: str,
        voice_data: CricketMatchDataExtraction | dict[str, Any],
        transcript: str,
        confidence_score: float,
        processing_duration: float,
    ) -> CricketMatchEntry:
        """Create cricket match entry from voice processing data."""
        try:
            # Handle both Pydantic model and dict input
            if isinstance(voice_data, CricketMatchDataExtraction):
                data = voice_data.model_dump()
            else:
                data = voice_data

            # Normalize match type
            match_type = self._normalize_match_type(data.get("match_type", "school"))

            # Create cricket match entry
            match_entry = CricketMatchEntry(
                session_id=session_id,
                user_id=user_id,
                # Voice processing metadata
                transcript=transcript,
                confidence_score=confidence_score,
                processing_duration=processing_duration,
                # Cricket match data
                match_type=match_type,
                opposition_strength=data.get("opposition_strength", 5),
                pre_match_nerves=data.get("pre_match_nerves", 5),
                post_match_satisfaction=data.get("post_match_satisfaction", 5),
                mental_state=data.get("mental_state", "good"),
                # Batting stats
                runs_scored=data.get("runs_scored"),
                balls_faced=data.get("balls_faced"),
                boundaries_4s=data.get("boundaries_4s"),
                boundaries_6s=data.get("boundaries_6s"),
                how_out=data.get("how_out"),
                key_shots_played=data.get("key_shots_played"),
                # Wicket keeping stats
                catches_taken=data.get("catches_taken"),
                catches_dropped=data.get("catches_dropped"),
                stumpings=data.get("stumpings"),
                notes=data.get("notes"),
            )

            self.session.add(match_entry)
            await self.session.commit()
            await self.session.refresh(match_entry)

            logger.info("Created cricket match entry from voice data: %s", match_entry.id)
            return match_entry

        except Exception as e:
            await self.session.rollback()
            logger.exception("Failed to create cricket match entry from voice data")
            msg = f"Failed to create cricket match entry: {e}"
            raise CricketRepositoryError(msg) from e

    def _to_read_schema(self, db_record: CricketMatchEntry) -> CricketMatchEntryRead:
        """Convert database model to read schema."""
        return CricketMatchEntryRead(
            id=db_record.id,
            session_id=db_record.session_id,
            user_id=db_record.user_id,
            match_type=db_record.match_type.value,
            opposition_strength=db_record.opposition_strength,
            pre_match_nerves=db_record.pre_match_nerves,
            post_match_satisfaction=db_record.post_match_satisfaction,
            mental_state=db_record.mental_state,
            runs_scored=db_record.runs_scored,
            balls_faced=db_record.balls_faced,
            boundaries_4s=db_record.boundaries_4s,
            boundaries_6s=db_record.boundaries_6s,
            how_out=db_record.how_out,
            key_shots_played=db_record.key_shots_played,
            catches_taken=db_record.catches_taken,
            catches_dropped=db_record.catches_dropped,
            stumpings=db_record.stumpings,
            notes=db_record.notes,
            transcript=db_record.transcript,
            confidence_score=db_record.confidence_score,
            processing_duration=db_record.processing_duration,
            created_at=db_record.created_at,
            updated_at=db_record.updated_at,
        )


class RestDayRepository(
    BaseRepository[RestDayEntry, RestDayEntryCreate, RestDayEntryRead, RestDayEntryUpdate],
):
    """Repository for rest day operations."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize rest day repository."""
        super().__init__(RestDayEntry, session)

    def _normalize_rest_type(self, rest_type: str) -> RestType:
        """Normalize rest type strings to valid RestType enum values."""
        rest_type_lower = rest_type.lower().strip()

        # Mapping of common variations to valid enum values
        rest_type_mapping = {
            # Complete rest variations
            "complete_rest": RestType.COMPLETE_REST,
            "complete rest": RestType.COMPLETE_REST,
            "full rest": RestType.COMPLETE_REST,
            "total rest": RestType.COMPLETE_REST,
            "no activity": RestType.COMPLETE_REST,
            "rest": RestType.COMPLETE_REST,
            "off": RestType.COMPLETE_REST,
            "lazy": RestType.COMPLETE_REST,
            "chill": RestType.COMPLETE_REST,
            # Active recovery variations
            "active_recovery": RestType.ACTIVE_RECOVERY,
            "active recovery": RestType.ACTIVE_RECOVERY,
            "light activity": RestType.ACTIVE_RECOVERY,
            "easy day": RestType.ACTIVE_RECOVERY,
            "gentle": RestType.ACTIVE_RECOVERY,
            "walk": RestType.ACTIVE_RECOVERY,
            "walking": RestType.ACTIVE_RECOVERY,
            "stretch": RestType.ACTIVE_RECOVERY,
            "stretching": RestType.ACTIVE_RECOVERY,
            "yoga": RestType.ACTIVE_RECOVERY,
            "mobility": RestType.ACTIVE_RECOVERY,
            # Injury recovery variations
            "injury_recovery": RestType.INJURY_RECOVERY,
            "injury recovery": RestType.INJURY_RECOVERY,
            "hurt": RestType.INJURY_RECOVERY,
            "injured": RestType.INJURY_RECOVERY,
            "pain": RestType.INJURY_RECOVERY,
            "sore": RestType.INJURY_RECOVERY,
            "rehab": RestType.INJURY_RECOVERY,
            "rehabilitation": RestType.INJURY_RECOVERY,
            "healing": RestType.INJURY_RECOVERY,
            "recovery": RestType.INJURY_RECOVERY,
        }

        normalized = rest_type_mapping.get(rest_type_lower)
        if normalized:
            return normalized

        # Try partial matching for compound terms
        if any(keyword in rest_type_lower for keyword in ["complete", "full", "total", "off"]):
            return RestType.COMPLETE_REST
        if any(
            keyword in rest_type_lower
            for keyword in ["active", "light", "gentle", "walk", "stretch", "yoga"]
        ):
            return RestType.ACTIVE_RECOVERY
        if any(
            keyword in rest_type_lower for keyword in ["injury", "hurt", "pain", "rehab", "healing"]
        ):
            return RestType.INJURY_RECOVERY

        # Default fallback
        logger.warning("Unknown rest type '%s', defaulting to 'complete_rest'", rest_type)
        return RestType.COMPLETE_REST

    async def create_from_voice_data(
        self,
        session_id: str,
        user_id: str,
        voice_data: RestDayDataExtraction | dict[str, Any],
        transcript: str,
        confidence_score: float,
        processing_duration: float,
    ) -> RestDayEntry:
        """Create rest day entry from voice processing data."""
        try:
            # Handle both Pydantic model and dict input
            if isinstance(voice_data, RestDayDataExtraction):
                data = voice_data.model_dump()
            else:
                data = voice_data

            # Normalize rest type
            rest_type = self._normalize_rest_type(data.get("rest_type", "complete_rest"))

            # Create rest day entry
            rest_entry = RestDayEntry(
                session_id=session_id,
                user_id=user_id,
                # Voice processing metadata
                transcript=transcript,
                confidence_score=confidence_score,
                processing_duration=processing_duration,
                # Rest day data
                rest_type=rest_type,
                physical_state=data.get("physical_state", ""),
                fatigue_level=data.get("fatigue_level", 5),
                energy_level=data.get("energy_level", 5),
                motivation_level=data.get("motivation_level", 5),
                mood_description=data.get("mood_description", ""),
                mental_state=data.get("mental_state", "good"),
                soreness_level=data.get("soreness_level"),
                training_reflections=data.get("training_reflections"),
                goals_concerns=data.get("goals_concerns"),
                recovery_activities=data.get("recovery_activities"),
                notes=data.get("notes"),
            )

            self.session.add(rest_entry)
            await self.session.commit()
            await self.session.refresh(rest_entry)

            logger.info("Created rest day entry from voice data: %s", rest_entry.id)
            return rest_entry

        except Exception as e:
            await self.session.rollback()
            logger.exception("Failed to create rest day entry from voice data")
            msg = f"Failed to create rest day entry: {e}"
            raise CricketRepositoryError(msg) from e

    def _to_read_schema(self, db_record: RestDayEntry) -> RestDayEntryRead:
        """Convert database model to read schema."""
        return RestDayEntryRead(
            id=db_record.id,
            session_id=db_record.session_id,
            user_id=db_record.user_id,
            rest_type=db_record.rest_type.value,
            physical_state=db_record.physical_state,
            fatigue_level=db_record.fatigue_level,
            energy_level=db_record.energy_level,
            motivation_level=db_record.motivation_level,
            mood_description=db_record.mood_description,
            mental_state=db_record.mental_state,
            soreness_level=db_record.soreness_level,
            training_reflections=db_record.training_reflections,
            goals_concerns=db_record.goals_concerns,
            recovery_activities=db_record.recovery_activities,
            notes=db_record.notes,
            transcript=db_record.transcript,
            confidence_score=db_record.confidence_score,
            processing_duration=db_record.processing_duration,
            created_at=db_record.created_at,
            updated_at=db_record.updated_at,
        )


class CricketAnalyticsRepository:
    """Repository for cricket-specific analytics operations."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize cricket analytics repository."""
        self.session = session

    async def get_cricket_analytics(
        self,
        user_id: str,
        days_back: int = 30,
    ) -> CricketAnalytics:
        """Generate comprehensive cricket analytics."""
        try:
            cutoff_date = datetime.now(UTC) - timedelta(days=days_back)

            # Get coaching session stats
            coaching_result = await self.session.execute(
                select(func.count(CricketCoachingEntry.id)).filter(
                    CricketCoachingEntry.user_id == user_id,
                    CricketCoachingEntry.created_at >= cutoff_date,
                ),
            )
            total_coaching_sessions = coaching_result.scalar() or 0

            # Get match stats
            match_result = await self.session.execute(
                select(func.count(CricketMatchEntry.id)).filter(
                    CricketMatchEntry.user_id == user_id,
                    CricketMatchEntry.created_at >= cutoff_date,
                ),
            )
            total_matches = match_result.scalar() or 0

            # Get rest day stats (import RestDayEntry if needed)
            from fitness_tracking.models.cricket import RestDayEntry

            rest_result = await self.session.execute(
                select(func.count(RestDayEntry.id)).filter(
                    RestDayEntry.user_id == user_id,
                    RestDayEntry.created_at >= cutoff_date,
                ),
            )
            total_rest_days = rest_result.scalar() or 0

            # Calculate averages
            avg_self_assessment = await self._calculate_average_self_assessment(
                user_id,
                cutoff_date,
            )
            batting_average = await self._calculate_batting_average(user_id, cutoff_date)
            keeping_success_rate = await self._calculate_keeping_success_rate(user_id, cutoff_date)

            # Get most practiced skill
            most_practiced_skill = await self._get_most_practiced_skill(user_id, cutoff_date)

            # Calculate confidence trend
            confidence_trend = await self._calculate_confidence_trend(user_id, cutoff_date)

            # Get improvement areas
            improvement_areas = await self._get_improvement_areas(user_id, cutoff_date)

            # Generate recommendations
            recommendations = await self._generate_cricket_recommendations(user_id, cutoff_date)

            return CricketAnalytics(
                total_coaching_sessions=total_coaching_sessions,
                total_matches=total_matches,
                total_rest_days=total_rest_days,
                average_self_assessment=round(avg_self_assessment, 1),
                batting_average=batting_average,
                keeping_success_rate=keeping_success_rate,
                most_practiced_skill=most_practiced_skill,
                confidence_trend=confidence_trend,
                improvement_areas=improvement_areas,
                recommendations=recommendations,
            )

        except Exception as e:
            logger.exception("Failed to generate cricket analytics")
            msg = f"Failed to generate cricket analytics: {e}"
            raise CricketRepositoryError(msg) from e

    async def _calculate_average_self_assessment(
        self,
        user_id: str,
        cutoff_date: datetime,
    ) -> float:
        """Calculate average self assessment score."""
        result = await self.session.execute(
            select(func.avg(CricketCoachingEntry.self_assessment_score)).filter(
                CricketCoachingEntry.user_id == user_id,
                CricketCoachingEntry.created_at >= cutoff_date,
                CricketCoachingEntry.self_assessment_score.is_not(None),
            ),
        )

        avg_score = result.scalar()
        return float(avg_score) if avg_score is not None else 5.0

    async def _calculate_batting_average(
        self,
        user_id: str,
        cutoff_date: datetime,
    ) -> float | None:
        """Calculate batting average from match data."""
        result = await self.session.execute(
            select(
                func.sum(CricketMatchEntry.runs_scored),
                func.count(CricketMatchEntry.id),
            ).filter(
                CricketMatchEntry.user_id == user_id,
                CricketMatchEntry.created_at >= cutoff_date,
                CricketMatchEntry.runs_scored.is_not(None),
            ),
        )

        row = result.fetchone()
        if row and row[0] is not None and row[1] > 0:
            total_runs = row[0]
            total_innings = row[1]
            return round(total_runs / total_innings, 2)

        return None

    async def _calculate_keeping_success_rate(
        self,
        user_id: str,
        cutoff_date: datetime,
    ) -> float | None:
        """Calculate wicket keeping success rate."""
        result = await self.session.execute(
            select(
                func.sum(CricketMatchEntry.catches_taken),
                func.sum(CricketMatchEntry.catches_dropped),
            ).filter(
                CricketMatchEntry.user_id == user_id,
                CricketMatchEntry.created_at >= cutoff_date,
                CricketMatchEntry.catches_taken.is_not(None),
            ),
        )

        row = result.fetchone()
        if row and row[0] is not None:
            catches_taken = row[0] or 0
            catches_dropped = row[1] or 0
            total_chances = catches_taken + catches_dropped

            if total_chances > 0:
                return round((catches_taken / total_chances) * 100, 1)

        return None

    async def _get_most_practiced_skill(
        self,
        user_id: str,
        cutoff_date: datetime,
    ) -> str:
        """Get the most practiced skill."""
        result = await self.session.execute(
            select(CricketCoachingEntry.skills_practiced).filter(
                CricketCoachingEntry.user_id == user_id,
                CricketCoachingEntry.created_at >= cutoff_date,
            ),
        )

        skills_list = [row[0] for row in result.fetchall() if row[0]]
        if not skills_list:
            return "No skills recorded"

        # Get most common skill (simple approach)
        skill_counts = {}
        for skill in skills_list:
            # Split by common delimiters and count each skill
            for individual_skill in skill.replace(",", " ").split():
                individual_skill = individual_skill.strip().lower()
                if individual_skill:
                    skill_counts[individual_skill] = skill_counts.get(individual_skill, 0) + 1

        if skill_counts:
            most_practiced = max(skill_counts.items(), key=lambda x: x[1])[0]
            return most_practiced.title()
        return "General practice"

    async def _calculate_confidence_trend(
        self,
        user_id: str,
        cutoff_date: datetime,
    ) -> dict[str, float]:
        """Calculate confidence trend over time."""
        result = await self.session.execute(
            select(
                CricketCoachingEntry.confidence_level,
                CricketCoachingEntry.created_at,
            )
            .filter(
                CricketCoachingEntry.user_id == user_id,
                CricketCoachingEntry.created_at >= cutoff_date,
            )
            .order_by(CricketCoachingEntry.created_at),
        )

        confidence_data = [(row[0], row[1]) for row in result.fetchall() if row[0] is not None]

        if len(confidence_data) < 2:
            return {"trend": 0.0, "average": 5.0}

        # Split into first and second half to calculate trend
        mid_point = len(confidence_data) // 2
        first_half_avg = sum(item[0] for item in confidence_data[:mid_point]) / mid_point
        second_half_avg = sum(item[0] for item in confidence_data[mid_point:]) / (
            len(confidence_data) - mid_point
        )

        trend = (
            round(((second_half_avg - first_half_avg) / first_half_avg) * 100, 1)
            if first_half_avg > 0
            else 0.0
        )
        overall_avg = round(sum(item[0] for item in confidence_data) / len(confidence_data), 1)

        return {"trend": trend, "average": overall_avg}

    async def _get_improvement_areas(
        self,
        user_id: str,
        cutoff_date: datetime,
    ) -> list[str]:
        """Get improvement areas from recent coaching sessions."""
        result = await self.session.execute(
            select(CricketCoachingEntry.areas_for_improvement)
            .filter(
                CricketCoachingEntry.user_id == user_id,
                CricketCoachingEntry.created_at >= cutoff_date,
            )
            .limit(5),  # Get most recent 5 sessions
        )

        improvement_areas = []
        for row in result.fetchall():
            if row[0]:
                # Split by common delimiters and extract individual areas
                areas = [
                    area.strip() for area in row[0].replace(",", ";").split(";") if area.strip()
                ]
                improvement_areas.extend(areas)

        # Return unique areas (up to 5 most recent)
        unique_areas = list(
            dict.fromkeys(improvement_areas),
        )  # Preserves order while removing duplicates
        return unique_areas[:5] if unique_areas else ["No specific areas identified"]

    async def _generate_cricket_recommendations(
        self,
        user_id: str,
        cutoff_date: datetime,
    ) -> list[str]:
        """Generate cricket-specific recommendations."""
        recommendations = []

        try:
            # Analyze confidence levels
            confidence_result = await self.session.execute(
                select(func.avg(CricketCoachingEntry.confidence_level)).filter(
                    CricketCoachingEntry.user_id == user_id,
                    CricketCoachingEntry.created_at >= cutoff_date,
                ),
            )

            confidence = confidence_result.scalar()
            if confidence and confidence < 6:
                recommendations.append(
                    "Focus on building confidence through regular practice and positive self-talk",
                )

            # Analyze frequency
            sessions_result = await self.session.execute(
                select(func.count(CricketCoachingEntry.id)).filter(
                    CricketCoachingEntry.user_id == user_id,
                    CricketCoachingEntry.created_at >= cutoff_date,
                ),
            )

            sessions = sessions_result.scalar() or 0
            days_period = (datetime.now(UTC) - cutoff_date).days
            frequency = sessions / days_period if days_period > 0 else 0

            if frequency < 0.2:  # Less than 2 sessions per 10 days
                recommendations.append(
                    "Try to increase your cricket practice frequency for better skill development",
                )

            if not recommendations:
                recommendations.append(
                    "Keep up the excellent cricket training! Your consistency is paying off",
                )

        except Exception:
            logger.exception("Error generating cricket recommendations")
            recommendations.append("Unable to generate cricket recommendations at this time")

        return recommendations
