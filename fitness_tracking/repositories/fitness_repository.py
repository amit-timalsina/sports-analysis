"""Fitness repository with analytics capabilities."""

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from common.exceptions import AppError
from common.repositories.base_repository import BaseRepository
from fitness_tracking.models.fitness import FitnessEntry, FitnessType, Intensity
from fitness_tracking.schemas.fitness import (
    FitnessAnalytics,
    FitnessDataExtraction,
    FitnessEntryCreate,
    FitnessEntryRead,
    FitnessEntryUpdate,
)

logger = logging.getLogger(__name__)


class FitnessRepositoryError(AppError):
    """Fitness repository specific error."""

    status_code = 500
    detail = "Fitness repository operation failed"


class FitnessRepository(
    BaseRepository[FitnessEntry, FitnessEntryCreate, FitnessEntryRead, FitnessEntryUpdate],
):
    """Repository for fitness entry operations with analytics."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize fitness repository."""
        super().__init__(FitnessEntry, session)

    def _normalize_intensity(self, intensity_value: str | None) -> Intensity:
        """Normalize AI-extracted intensity values to valid enum values."""
        if not intensity_value:
            return Intensity.MEDIUM

        intensity_lower = intensity_value.lower().strip()

        # Mapping of AI variations to valid enum values
        intensity_mapping = {
            # Low intensity variations
            "low": Intensity.LOW,
            "very light": Intensity.LOW,
            "light": Intensity.LOW,
            "easy": Intensity.LOW,
            "gentle": Intensity.LOW,
            "minimal": Intensity.LOW,
            "relaxed": Intensity.LOW,
            # Medium intensity variations
            "medium": Intensity.MEDIUM,
            "moderate": Intensity.MEDIUM,
            "normal": Intensity.MEDIUM,
            "average": Intensity.MEDIUM,
            "standard": Intensity.MEDIUM,
            # High intensity variations
            "high": Intensity.HIGH,
            "intense": Intensity.HIGH,
            "hard": Intensity.HIGH,
            "tough": Intensity.HIGH,
            "challenging": Intensity.HIGH,
            "vigorous": Intensity.HIGH,
            "difficult": Intensity.HIGH,
            "heavy": Intensity.HIGH,
        }

        # Try exact match first
        if intensity_lower in intensity_mapping:
            return intensity_mapping[intensity_lower]

        # Try partial matches for compound descriptions
        if any(word in intensity_lower for word in ["very", "extremely", "super"]):
            if any(word in intensity_lower for word in ["light", "easy", "low"]):
                return Intensity.LOW
            if any(word in intensity_lower for word in ["hard", "intense", "high"]):
                return Intensity.HIGH

        # Default fallback
        logger.warning("Unknown intensity value '%s', defaulting to MEDIUM", intensity_value)
        return Intensity.MEDIUM

    def _normalize_fitness_type(self, fitness_type_value: str | None) -> FitnessType:
        """Normalize AI-extracted fitness type values to valid enum values."""
        if not fitness_type_value:
            return FitnessType.GENERAL_FITNESS

        fitness_lower = fitness_type_value.lower().strip()

        # Mapping of AI variations to valid enum values
        fitness_mapping = {
            # Running variations
            "running": FitnessType.RUNNING,
            "run": FitnessType.RUNNING,
            "jog": FitnessType.RUNNING,
            "jogging": FitnessType.RUNNING,
            "sprint": FitnessType.RUNNING,
            "sprinting": FitnessType.RUNNING,
            # Strength training variations
            "strength_training": FitnessType.STRENGTH_TRAINING,
            "strength training": FitnessType.STRENGTH_TRAINING,
            "weights": FitnessType.STRENGTH_TRAINING,
            "weight training": FitnessType.STRENGTH_TRAINING,
            "gym": FitnessType.STRENGTH_TRAINING,
            "lifting": FitnessType.STRENGTH_TRAINING,
            "weight lifting": FitnessType.STRENGTH_TRAINING,
            # Cricket specific variations
            "cricket_specific": FitnessType.CRICKET_SPECIFIC,
            "cricket specific": FitnessType.CRICKET_SPECIFIC,
            "cricket training": FitnessType.CRICKET_SPECIFIC,
            "cricket fitness": FitnessType.CRICKET_SPECIFIC,
            # Cardio variations
            "cardio": FitnessType.CARDIO,
            "cardiovascular": FitnessType.CARDIO,
            "aerobic": FitnessType.CARDIO,
            "cycling": FitnessType.CARDIO,
            "swimming": FitnessType.CARDIO,
            # Flexibility variations
            "flexibility": FitnessType.FLEXIBILITY,
            "stretching": FitnessType.FLEXIBILITY,
            "yoga": FitnessType.FLEXIBILITY,
            "pilates": FitnessType.FLEXIBILITY,
            # General fitness variations
            "general_fitness": FitnessType.GENERAL_FITNESS,
            "general fitness": FitnessType.GENERAL_FITNESS,
            "fitness": FitnessType.GENERAL_FITNESS,
            "workout": FitnessType.GENERAL_FITNESS,
            "exercise": FitnessType.GENERAL_FITNESS,
        }

        # Try exact match first
        if fitness_lower in fitness_mapping:
            return fitness_mapping[fitness_lower]

        # Try partial matches
        for key, value in fitness_mapping.items():
            if key in fitness_lower or fitness_lower in key:
                return value

        # Default fallback
        logger.warning(
            "Unknown fitness type value '%s', defaulting to GENERAL_FITNESS",
            fitness_type_value,
        )
        return FitnessType.GENERAL_FITNESS

    def _normalize_energy_level(self, energy_value: Any) -> int:
        """Normalize AI-extracted energy level values to valid 1-5 range."""
        if energy_value is None:
            return 3  # Default to middle value

        # Handle different input types
        if isinstance(energy_value, str):
            energy_lower = energy_value.lower().strip()

            # Text-based energy descriptions
            text_mapping = {
                "very low": 1,
                "low": 1,
                "poor": 1,
                "tired": 1,
                "exhausted": 1,
                "below average": 2,
                "somewhat low": 2,
                "fair": 2,
                "average": 3,
                "medium": 3,
                "normal": 3,
                "okay": 3,
                "moderate": 3,
                "good": 4,
                "high": 4,
                "energetic": 4,
                "strong": 4,
                "very high": 5,
                "excellent": 5,
                "amazing": 5,
                "outstanding": 5,
                "fantastic": 5,
            }

            if energy_lower in text_mapping:
                return text_mapping[energy_lower]

            # Try to extract number from string
            import re

            number_match = re.search(r"(\d+)", energy_value)
            if number_match:
                try:
                    energy_value = int(number_match.group(1))
                except ValueError:
                    return 3

        # Handle numeric values
        try:
            energy_int = int(float(energy_value))
            # Clamp to valid range 1-5
            return max(1, min(5, energy_int))
        except (ValueError, TypeError):
            logger.warning("Invalid energy level value '%s', defaulting to 3", energy_value)
            return 3

    async def create_from_voice_data(
        self,
        session_id: str,
        user_id: str,
        voice_data: FitnessDataExtraction | dict[str, Any],
        transcript: str,
        confidence_score: float,
        processing_duration: float,
    ) -> FitnessEntry:
        """Create fitness entry from voice processing data."""
        try:
            # Handle both Pydantic model and dict input
            if isinstance(voice_data, FitnessDataExtraction):
                data = voice_data.model_dump()
            else:
                data = voice_data

            # Create fitness entry with normalized data
            fitness_entry = FitnessEntry(
                session_id=session_id,
                user_id=user_id,
                # Voice processing metadata
                transcript=transcript,
                confidence_score=confidence_score,
                processing_duration=processing_duration,
                # Fitness data - all normalized
                fitness_type=self._normalize_fitness_type(data.get("fitness_type")),
                duration_minutes=max(1, int(data.get("duration_minutes", 0))),  # Ensure positive
                intensity=self._normalize_intensity(data.get("intensity")),
                details=data.get("details", ""),
                mental_state=data.get("mental_state", "good"),
                energy_level=self._normalize_energy_level(data.get("energy_level")),
                distance_km=data.get("distance_km"),
                location=data.get("location"),
                notes=data.get("notes"),
            )

            self.session.add(fitness_entry)
            await self.session.commit()
            await self.session.refresh(fitness_entry)

            logger.info("Created fitness entry from voice data: %s", fitness_entry.id)
        except Exception as e:
            await self.session.rollback()
            logger.exception("Failed to create fitness entry from voice data")
            msg = f"Failed to create fitness entry: {e}"
            raise FitnessRepositoryError(msg) from e
        else:
            return fitness_entry

    async def get_recent_entries(
        self,
        user_id: str,
        limit: int = 10,
        days_back: int = 30,
    ) -> list[FitnessEntryRead]:
        """Get recent fitness entries for a user."""
        try:
            cutoff_date = datetime.now(UTC) - timedelta(days=days_back)

            result = await self.session.execute(
                select(FitnessEntry)
                .filter(
                    FitnessEntry.user_id == user_id,
                    FitnessEntry.created_at >= cutoff_date,
                )
                .order_by(desc(FitnessEntry.created_at))
                .limit(limit),
            )

            entries = result.scalars().all()
            return [self._to_read_schema(entry) for entry in entries]

        except Exception as e:
            logger.exception("Failed to get recent fitness entries")
            msg = f"Failed to get recent fitness entries: {e}"
            raise FitnessRepositoryError(msg) from e

    async def get_fitness_analytics(
        self,
        user_id: str,
        days_back: int = 30,
    ) -> FitnessAnalytics:
        """Generate comprehensive fitness analytics."""
        try:
            cutoff_date = datetime.now(UTC) - timedelta(days=days_back)

            # Get all entries in the period
            result = await self.session.execute(
                select(FitnessEntry)
                .filter(
                    FitnessEntry.user_id == user_id,
                    FitnessEntry.created_at >= cutoff_date,
                )
                .order_by(FitnessEntry.created_at),
            )

            entries = list(result.scalars().all())

            if not entries:
                return FitnessAnalytics(
                    total_sessions=0,
                    total_duration_minutes=0,
                    average_duration_minutes=0.0,
                    total_distance_km=None,
                    average_intensity_score=0.0,
                    average_energy_level=0.0,
                    most_common_activity="none",
                    weekly_frequency=0.0,
                    improvement_trends={},
                    recommendations=[],
                )

            # Calculate analytics
            total_sessions = len(entries)
            weeks_in_period = days_back / 7
            weekly_frequency = total_sessions / weeks_in_period

            # Duration calculations
            total_duration_minutes = sum(
                entry.duration_minutes for entry in entries if entry.duration_minutes
            )
            average_duration_minutes = (
                total_duration_minutes / total_sessions if total_sessions > 0 else 0.0
            )

            # Distance calculations
            distances = [entry.distance_km for entry in entries if entry.distance_km is not None]
            total_distance_km = sum(distances) if distances else None

            avg_intensity = await self._calculate_average_intensity_score(
                user_id,
                cutoff_date,
            )
            avg_energy = await self._calculate_average_energy_level(user_id, cutoff_date)

            # Most common activity
            activity_counts = {}
            for entry in entries:
                activity = entry.fitness_type.value
                activity_counts[activity] = activity_counts.get(activity, 0) + 1

            most_common = (
                max(activity_counts.items(), key=lambda x: x[1])[0] if activity_counts else "none"
            )

            # Calculate improvement trends
            improvement_trends = await self._calculate_improvement_trends(user_id, cutoff_date)

            # Generate recommendations
            recommendations = await self._generate_fitness_recommendations(
                user_id,
                cutoff_date,
                weekly_frequency,
                avg_energy,
            )

            return FitnessAnalytics(
                total_sessions=total_sessions,
                total_duration_minutes=total_duration_minutes,
                average_duration_minutes=round(average_duration_minutes, 1),
                total_distance_km=round(total_distance_km, 2) if total_distance_km else None,
                average_intensity_score=round(avg_intensity, 2),
                average_energy_level=round(avg_energy, 1),
                most_common_activity=most_common,
                weekly_frequency=round(weekly_frequency, 2),
                improvement_trends=improvement_trends,
                recommendations=recommendations,
            )

        except Exception as e:
            logger.exception("Failed to generate fitness analytics")
            msg = f"Failed to generate fitness analytics: {e}"
            raise FitnessRepositoryError(msg) from e

    async def _calculate_average_intensity_score(
        self,
        user_id: str,
        cutoff_date: datetime,
    ) -> float:
        """Calculate average intensity score (low=1, medium=2, high=3)."""
        result = await self.session.execute(
            select(FitnessEntry.intensity).filter(
                FitnessEntry.user_id == user_id,
                FitnessEntry.created_at >= cutoff_date,
            ),
        )

        intensities = [row[0] for row in result.fetchall()]
        if not intensities:
            return 0.0

        intensity_scores = {
            Intensity.LOW: 1,
            Intensity.MEDIUM: 2,
            Intensity.HIGH: 3,
        }

        total_score = sum(intensity_scores.get(intensity, 2) for intensity in intensities)
        return total_score / len(intensities)

    async def _calculate_average_energy_level(self, user_id: str, cutoff_date: datetime) -> float:
        """Calculate average energy level."""
        result = await self.session.execute(
            select(func.avg(FitnessEntry.energy_level)).filter(
                FitnessEntry.user_id == user_id,
                FitnessEntry.created_at >= cutoff_date,
                FitnessEntry.energy_level.is_not(None),
            ),
        )

        avg_energy = result.scalar()
        return float(avg_energy) if avg_energy is not None else 3.0

    async def _calculate_improvement_trends(
        self,
        user_id: str,
        cutoff_date: datetime,
    ) -> dict[str, float]:
        """Calculate improvement trends over time."""
        trends = {}

        try:
            # Get entries ordered by date
            result = await self.session.execute(
                select(FitnessEntry)
                .filter(
                    FitnessEntry.user_id == user_id,
                    FitnessEntry.created_at >= cutoff_date,
                )
                .order_by(FitnessEntry.created_at),
            )

            entries = list(result.scalars().all())
            if len(entries) < 2:
                return {"overall_trend": 0.0}  # 0.0 for insufficient data

            # Split into first and second half
            mid_point = len(entries) // 2
            first_half = entries[:mid_point]
            second_half = entries[mid_point:]

            # Duration trend (percentage change)
            first_avg_duration = sum(
                e.duration_minutes for e in first_half if e.duration_minutes
            ) / len(first_half)
            second_avg_duration = sum(
                e.duration_minutes for e in second_half if e.duration_minutes
            ) / len(second_half)

            if first_avg_duration > 0:
                duration_change = (
                    (second_avg_duration - first_avg_duration) / first_avg_duration
                ) * 100
                trends["duration_change_percent"] = round(duration_change, 1)

            # Energy level trend (percentage change)
            first_avg_energy = sum(e.energy_level for e in first_half if e.energy_level) / len(
                first_half,
            )
            second_avg_energy = sum(e.energy_level for e in second_half if e.energy_level) / len(
                second_half,
            )

            if first_avg_energy > 0:
                energy_change = ((second_avg_energy - first_avg_energy) / first_avg_energy) * 100
                trends["energy_change_percent"] = round(energy_change, 1)

            # Overall trend score (average of available metrics)
            if trends:
                overall_trend = sum(trends.values()) / len(trends)
                trends["overall_trend"] = round(overall_trend, 1)
            else:
                trends["overall_trend"] = 0.0

        except Exception:
            logger.exception("Error calculating improvement trends")
            trends["overall_trend"] = 0.0  # 0.0 for calculation error

        return trends

    async def _generate_fitness_recommendations(
        self,
        user_id: str,
        cutoff_date: datetime,
        frequency: float,
        energy_level: float | None,
    ) -> list[str]:
        """Generate fitness recommendations based on user data."""
        recommendations = []

        try:
            # Frequency recommendations
            if frequency < 0.3:  # Less than 3 sessions per 10 days
                recommendations.append(
                    "Try to increase your fitness frequency to at least 3-4 sessions per week",
                )

            # Energy level recommendations
            if energy_level and energy_level < 3:
                recommendations.append(
                    "Your energy levels seem low. Consider adjusting workout intensity or getting more rest",
                )

            # Variety recommendations
            result = await self.session.execute(
                select(func.count(func.distinct(FitnessEntry.fitness_type))).filter(
                    FitnessEntry.user_id == user_id,
                    FitnessEntry.created_at >= cutoff_date,
                ),
            )

            variety_count = result.scalar() or 0
            sessions_result = await self.session.execute(
                select(func.count(FitnessEntry.id)).filter(
                    FitnessEntry.user_id == user_id,
                    FitnessEntry.created_at >= cutoff_date,
                ),
            )
            sessions = sessions_result.scalar() or 0

            if variety_count <= 1 and sessions > 5:
                recommendations.append(
                    "Try adding variety to your workouts with different types of fitness activities",
                )

            if not recommendations:
                recommendations.append(
                    "Keep up the great work! Your fitness routine looks well-balanced",
                )

        except Exception:
            logger.exception("Error generating fitness recommendations")
            recommendations.append("Unable to generate recommendations at this time")

        return recommendations

    def _to_read_schema(self, db_record: FitnessEntry) -> FitnessEntryRead:
        """Convert database model to read schema."""
        return FitnessEntryRead(
            id=db_record.id,
            session_id=db_record.session_id,
            user_id=db_record.user_id,
            fitness_type=db_record.fitness_type.value,
            duration_minutes=db_record.duration_minutes,
            intensity=db_record.intensity.value,
            details=db_record.details,
            mental_state=db_record.mental_state,
            energy_level=db_record.energy_level,
            distance_km=db_record.distance_km,
            location=db_record.location,
            notes=db_record.notes,
            transcript=db_record.transcript,
            confidence_score=db_record.confidence_score,
            processing_duration=db_record.processing_duration,
            created_at=db_record.created_at,
            updated_at=db_record.updated_at,
        )
