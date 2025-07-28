"""Tests for fitness tracking schemas."""

import uuid

import pytest
from pydantic import ValidationError

from common.schemas.entry_type import EntryType
from fitness_tracking.schemas.exercise_type import ExerciseType
from fitness_tracking.schemas.fitness import FitnessEntryCreate
from fitness_tracking.schemas.fitness_data_extraction import FitnessDataExtraction
from fitness_tracking.schemas.intensity_level import IntensityLevel


class TestFitnessEntryCreate:
    """Test cases for FitnessEntryCreate schema."""

    def test_valid_fitness_entry(self):
        """Test creating a valid fitness entry."""
        entry_data = {
            "user_id": "user123",
            "session_id": "session123",
            "conversation_id": uuid.uuid4(),
            "entry_type": EntryType.FITNESS,
            "original_transcript": "I went for a run",
            "overall_confidence_score": 0.95,
            "mental_state": "good",
            "exercise_type": ExerciseType.CARDIO,
            "exercise_name": "Running",
            "duration_minutes": 30,
            "distance_km": 5.0,
            "intensity": IntensityLevel.MODERATE,
            "heart_rate_avg": 140,
            "heart_rate_max": 160,
            "location": "Central Park",
            "energy_level": 4,
        }

        entry = FitnessEntryCreate(**entry_data)

        assert entry.exercise_type == ExerciseType.CARDIO
        assert entry.duration_minutes == 30
        assert entry.distance_km == 5.0
        assert entry.intensity == IntensityLevel.MODERATE
        assert entry.energy_level == 4

    def test_minimum_required_fields(self):
        """Test creating entry with only required fields."""
        entry_data = {
            "user_id": "user123",
            "session_id": "session123",
            "conversation_id": uuid.uuid4(),
            "entry_type": EntryType.FITNESS,
            "original_transcript": "I did strength training",
            "overall_confidence_score": 0.9,
            "mental_state": "excellent",
            "exercise_type": ExerciseType.STRENGTH,
            "exercise_name": "Weight Training",
            "duration_minutes": 45,
            "intensity": IntensityLevel.HIGH,
        }

        entry = FitnessEntryCreate(**entry_data)

        assert entry.exercise_type == ExerciseType.STRENGTH
        assert entry.distance_km is None
        assert entry.calories_burned is None

    def test_invalid_duration_too_short(self):
        """Test validation fails for duration too short."""
        entry_data = {
            "user_id": "user123",
            "session_id": "session123",
            "conversation_id": uuid.uuid4(),
            "entry_type": EntryType.FITNESS,
            "original_transcript": "Quick run",
            "overall_confidence_score": 0.9,
            "mental_state": "good",
            "exercise_type": ExerciseType.CARDIO,
            "exercise_name": "Running",
            "duration_minutes": 0,  # Invalid: too short
            "intensity": IntensityLevel.MODERATE,
        }

        with pytest.raises(ValidationError) as exc_info:
            FitnessEntryCreate(**entry_data)

        assert "Input should be greater than 0" in str(exc_info.value)

    def test_invalid_energy_level_out_of_range(self):
        """Test validation fails for energy level out of range."""
        entry_data = {
            "user_id": "user123",
            "session_id": "session123",
            "conversation_id": uuid.uuid4(),
            "entry_type": EntryType.FITNESS,
            "original_transcript": "Light workout",
            "overall_confidence_score": 0.9,
            "mental_state": "okay",
            "exercise_type": ExerciseType.STRENGTH,
            "exercise_name": "Light Training",
            "duration_minutes": 30,
            "intensity": IntensityLevel.LOW,
            "energy_level": 11,  # Invalid: too high
        }

        with pytest.raises(ValidationError) as exc_info:
            FitnessEntryCreate(**entry_data)

        assert "Input should be less than or equal to 10" in str(exc_info.value)

    def test_heart_rate_consistency_validation(self):
        """Test heart rate consistency validation."""
        entry_data = {
            "user_id": "user123",
            "session_id": "session123",
            "conversation_id": uuid.uuid4(),
            "entry_type": EntryType.FITNESS,
            "original_transcript": "Interval training",
            "overall_confidence_score": 0.9,
            "mental_state": "good",
            "exercise_type": ExerciseType.CARDIO,
            "exercise_name": "HIIT",
            "duration_minutes": 45,
            "intensity": IntensityLevel.HIGH,
            "heart_rate_avg": 180,  # Invalid: higher than max
            "heart_rate_max": 160,
        }

        with pytest.raises(ValidationError) as exc_info:
            FitnessEntryCreate(**entry_data)

        assert "Maximum heart rate cannot be less than average heart rate" in str(exc_info.value)

    def test_cricket_specific_activity_type(self):
        """Test cricket-specific fitness activity."""
        entry_data = {
            "user_id": "user123",
            "session_id": "session123",
            "conversation_id": uuid.uuid4(),
            "entry_type": EntryType.FITNESS,
            "original_transcript": "Cricket practice",
            "overall_confidence_score": 0.9,
            "mental_state": "excellent",
            "exercise_type": ExerciseType.SPORTS,
            "exercise_name": "Cricket Training",
            "duration_minutes": 60,
            "intensity": IntensityLevel.MODERATE,
            "energy_level": 4,
            "location": "Cricket ground",
        }

        entry = FitnessEntryCreate(**entry_data)

        assert entry.exercise_type == ExerciseType.SPORTS
        assert entry.location == "Cricket ground"


class TestFitnessDataExtraction:
    """Test cases for FitnessDataExtraction schema."""

    def test_valid_extraction_data(self):
        """Test creating valid fitness data extraction."""
        extraction_data = {
            "fitness_type": "running",
            "duration_minutes": 25,
            "intensity": "low",
            "details": "Easy pace run",
            "mental_state": "good",
            "energy_level": 3,
            "distance_km": 4.5,
            "location": "neighborhood",
        }

        extraction = FitnessDataExtraction(**extraction_data)

        assert extraction.fitness_type == "running"
        assert extraction.duration_minutes == 25
        assert extraction.distance_km == 4.5

    def test_minimal_extraction_data(self):
        """Test creating extraction with minimal required fields."""
        extraction_data = {
            "fitness_type": "strength_training",
            "duration_minutes": 40,
            "intensity": "high",
            "details": "Upper body workout",
            "mental_state": "focused",
            "energy_level": 4,
        }

        extraction = FitnessDataExtraction(**extraction_data)

        assert extraction.fitness_type == "strength_training"
        assert extraction.distance_km is None
        assert extraction.calories_burned is None


if __name__ == "__main__":
    pytest.main([__file__])
