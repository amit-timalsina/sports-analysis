"""Tests for fitness tracking schemas."""

import pytest
from pydantic import ValidationError

from fitness_tracking.schemas.fitness import FitnessDataExtraction, FitnessEntryCreate


class TestFitnessEntryCreate:
    """Test cases for FitnessEntryCreate schema."""

    def test_valid_fitness_entry(self):
        """Test creating a valid fitness entry."""
        entry_data = {
            "type": "running",
            "duration_minutes": 30,
            "distance_km": 5.0,
            "intensity": "medium",
            "details": "Morning run in the park",
            "mental_state": "good",
            "energy_level": 4,
            "heart_rate_avg": 140,
            "heart_rate_max": 160,
            "location": "Central Park",
        }

        entry = FitnessEntryCreate(**entry_data)

        assert entry.type == "running"
        assert entry.duration_minutes == 30
        assert entry.distance_km == 5.0
        assert entry.intensity == "medium"
        assert entry.energy_level == 4

    def test_minimum_required_fields(self):
        """Test creating entry with only required fields."""
        entry_data = {
            "type": "gym",
            "duration_minutes": 45,
            "intensity": "high",
            "details": "Strength training session",
            "mental_state": "excellent",
            "energy_level": 5,
        }

        entry = FitnessEntryCreate(**entry_data)

        assert entry.type == "gym"
        assert entry.distance_km is None
        assert entry.calories_burned is None

    def test_invalid_duration_too_short(self):
        """Test validation fails for duration too short."""
        entry_data = {
            "type": "running",
            "duration_minutes": 0,  # Invalid: too short
            "intensity": "medium",
            "details": "Test run",
            "mental_state": "good",
            "energy_level": 3,
        }

        with pytest.raises(ValidationError) as exc_info:
            FitnessEntryCreate(**entry_data)

        assert "greater than or equal to 1" in str(exc_info.value)

    def test_invalid_energy_level_out_of_range(self):
        """Test validation fails for energy level out of range."""
        entry_data = {
            "type": "gym",
            "duration_minutes": 30,
            "intensity": "low",
            "details": "Light workout",
            "mental_state": "okay",
            "energy_level": 6,  # Invalid: too high
        }

        with pytest.raises(ValidationError) as exc_info:
            FitnessEntryCreate(**entry_data)

        assert "less than or equal to 5" in str(exc_info.value)

    def test_heart_rate_consistency_validation(self):
        """Test heart rate consistency validation."""
        entry_data = {
            "type": "cardio",
            "duration_minutes": 45,
            "intensity": "high",
            "details": "Interval training",
            "mental_state": "good",
            "energy_level": 4,
            "heart_rate_avg": 180,  # Invalid: higher than max
            "heart_rate_max": 160,
        }

        with pytest.raises(ValidationError) as exc_info:
            FitnessEntryCreate(**entry_data)

        assert "cannot be less than average" in str(exc_info.value)

    def test_cricket_specific_activity_type(self):
        """Test cricket-specific fitness activity."""
        entry_data = {
            "type": "cricket_specific",
            "duration_minutes": 60,
            "intensity": "medium",
            "details": "Wicket keeping practice with fitness drills",
            "mental_state": "excellent",
            "energy_level": 4,
            "location": "Cricket ground",
        }

        entry = FitnessEntryCreate(**entry_data)

        assert entry.type == "cricket_specific"
        assert entry.location == "Cricket ground"


class TestFitnessDataExtraction:
    """Test cases for FitnessDataExtraction schema."""

    def test_valid_extraction_data(self):
        """Test creating valid fitness data extraction."""
        extraction_data = {
            "fitness_type": "running",
            "duration_minutes": 25,
            "intensity": "medium",
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
